import math


class StepwiseNelderMead2D:
	"""
	Nelder-Mead simplex optimizer for two variables, designed for sequential
	environments where exactly one function evaluation is available per step.

	The optimizer **maximizes** the objective.  Call advance() once per step:
	pass in the value observed at the last proposed point (None on the first
	call) and receive the next (x, y) point to evaluate.

	Standard NM coefficients follow Nelder & Mead (1965):
	  alpha = 1.0  reflection
	  gamma = 2.0  expansion
	  beta  = 0.5  contraction
	  delta = 0.5  shrink

	Initialization requires exactly three seed points to form the initial
	simplex; the first reflect is proposed after all three are evaluated.
	The shrink step evaluates two points across two consecutive calls.

	For a time-varying objective, ``min_simplex_size`` and ``max_vertex_age``
	opt into a tracking mode.  A too-small simplex or an over-age stored value
	causes a fresh regular simplex to be evaluated around the current operating
	point.  With ``use_log_coordinates=True``, simplex geometry is computed in
	log space, so sizes represent proportional changes in positive variables.
	After the first restart, ``max_proposal_step`` can limit the distance of one
	proposal from the point that was just evaluated, preventing expansion bursts.
	"""

	def __init__(self, seeds, lower_bounds=(0.0, 0.0),
				 alpha=1.0, gamma=2.0, beta=0.5, delta=0.5,
				 min_simplex_size=None, max_vertex_age=None,
				 restart_rotation=math.pi / 6, use_log_coordinates=False,
				 max_proposal_step=None):
		if len(seeds) != 3:
			raise ValueError('exactly 3 seed points are required for a 2-D simplex')
		if min_simplex_size is not None and min_simplex_size <= 0:
			raise ValueError('min_simplex_size must be positive')
		if max_vertex_age is not None:
			if min_simplex_size is None:
				raise ValueError('max_vertex_age requires min_simplex_size')
			if not isinstance(max_vertex_age, int) or max_vertex_age < 3:
				raise ValueError('max_vertex_age must be an integer of at least 3')
		if max_proposal_step is not None:
			if min_simplex_size is None:
				raise ValueError('max_proposal_step requires min_simplex_size')
			if max_proposal_step < min_simplex_size:
				raise ValueError('max_proposal_step must be at least min_simplex_size')
		if use_log_coordinates:
			if any(bound <= 0 for bound in lower_bounds):
				raise ValueError('log coordinates require positive lower bounds')
			if any(x <= 0 or y <= 0 for x, y in seeds):
				raise ValueError('log coordinates require positive seed coordinates')

		self._use_log_coordinates = use_log_coordinates
		self._seeds = [list(self._to_internal(*s)) for s in seeds]
		self._lb = self._to_internal(*lower_bounds)
		self._alpha = alpha
		self._gamma = gamma
		self._beta = beta
		self._delta = delta
		self._min_simplex_size = min_simplex_size
		self._max_vertex_age = max_vertex_age
		self._restart_rotation = restart_rotation
		self._max_proposal_step = max_proposal_step

		self._vertices = []       # [x, y, value, evaluation_count] entries
		self._pending = None      # [x, y] most recently proposed point
		self._action = 'init'
		self._saved = None        # ([x, y], value, step) for expand / outside-contract
		self._shrink_buf = None   # first shrunk vertex held during two-step shrink
		self._init_idx = 0        # next seed index to propose (0–2 during init)
		self._evaluation_count = 0
		self._restart_count = 0
		self._last_restart_reason = None

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------

	def advance(self, observed_value):
		"""
		Feed the objective value observed at the last proposed point, update
		the simplex, and return the next (x, y) point to evaluate.
		Pass None on the very first call.
		"""
		if self._pending is not None and observed_value is not None:
			self._evaluation_count += 1

		if self._action == 'init':
			evaluated_point = self._pending[:] if observed_value is not None else None
			self._advance_init(observed_value)
			self._limit_pending_step(evaluated_point)
			return self._external_pending()
		if observed_value is not None:
			evaluated_point = self._pending[:]
			self._process(observed_value)
			self._maybe_restart(evaluated_point)
			self._limit_pending_step(evaluated_point)
		return self._external_pending()

	@property
	def best(self):
		"""Best [x, y, value] triple seen so far, or None before init completes."""
		if not self._vertices:
			return None
		vertex = max(self._vertices, key=lambda v: v[2])
		x, y = self._to_external(vertex[0], vertex[1])
		return [x, y, vertex[2]]

	@property
	def tracking_enabled(self):
		"""Whether floor-restart tracking is enabled."""
		return self._min_simplex_size is not None

	@property
	def restart_count(self):
		"""Number of floor or vertex-age restarts performed."""
		return self._restart_count

	@property
	def last_restart_reason(self):
		"""Reason for the most recent restart, or None if none occurred."""
		return self._last_restart_reason

	@property
	def simplex_size(self):
		"""Current simplex radius in the configured coordinate system."""
		if len(self._vertices) != 3:
			return None
		cx = sum(v[0] for v in self._vertices) / 3
		cy = sum(v[1] for v in self._vertices) / 3
		return max(math.hypot(v[0] - cx, v[1] - cy) for v in self._vertices)

	@property
	def oldest_vertex_age(self):
		"""Age in evaluations of the oldest current vertex, or None."""
		if not self._vertices:
			return None
		return max(self._evaluation_count - v[3] for v in self._vertices)

	# ------------------------------------------------------------------
	# Initialisation phase
	# ------------------------------------------------------------------

	def _advance_init(self, observed_value):
		if self._init_idx == 0:
			x, y = self._clamp(*self._seeds[0])
			self._pending = [x, y]
			self._init_idx = 1
			return self._external_pending()

		self._vertices.append([
			self._pending[0], self._pending[1], observed_value,
			self._evaluation_count,
		])

		if self._init_idx < 3:
			x, y = self._clamp(*self._seeds[self._init_idx])
			self._pending = [x, y]
			self._init_idx += 1
			return self._external_pending()

		# All three seeds evaluated; enter running phase.
		self._action = 'reflect'
		self._propose_reflect()
		return self._external_pending()

	# ------------------------------------------------------------------
	# Running phase
	# ------------------------------------------------------------------

	def _process(self, value):
		self._vertices.sort(key=lambda v: -v[2])
		best_val   = self._vertices[0][2]
		second_val = self._vertices[1][2]
		worst_val  = self._vertices[2][2]

		if self._action == 'reflect':
			if value > best_val:
				self._propose_expand(value)
			elif value > second_val:
				self._replace_worst(value)
				self._propose_reflect()
			elif value > worst_val:
				self._propose_outside_contract(value)
			else:
				self._propose_inside_contract()

		elif self._action == 'expand':
			r_pt, r_val, r_step = self._saved
			if value > r_val:
				self._replace_worst(value)
			else:
				self._vertices[2] = [r_pt[0], r_pt[1], r_val, r_step]
			self._propose_reflect()

		elif self._action == 'outside_contract':
			_, r_val, _ = self._saved
			if value >= r_val:
				self._replace_worst(value)
				self._propose_reflect()
			else:
				self._propose_shrink(vertex_idx=1)

		elif self._action == 'inside_contract':
			if value > worst_val:
				self._replace_worst(value)
				self._propose_reflect()
			else:
				self._propose_shrink(vertex_idx=1)

		elif self._action == 'shrink_1':
			self._shrink_buf = [
				self._pending[0], self._pending[1], value,
				self._evaluation_count,
			]
			self._propose_shrink(vertex_idx=2)

		elif self._action == 'shrink_2':
			self._vertices[1] = self._shrink_buf
			self._replace_worst(value)
			self._propose_reflect()

	# ------------------------------------------------------------------
	# Proposal helpers
	# ------------------------------------------------------------------

	def _propose_reflect(self):
		self._vertices.sort(key=lambda v: -v[2])
		cx, cy = self._centroid()
		wx, wy = self._vertices[2][0], self._vertices[2][1]
		rx = cx + self._alpha * (cx - wx)
		ry = cy + self._alpha * (cy - wy)
		self._pending = list(self._clamp(rx, ry))
		self._action = 'reflect'

	def _propose_expand(self, reflect_value):
		# self._pending is currently the reflect point
		self._saved = (self._pending[:], reflect_value, self._evaluation_count)
		cx, cy = self._centroid()
		ex = cx + self._gamma * (self._pending[0] - cx)
		ey = cy + self._gamma * (self._pending[1] - cy)
		self._pending = list(self._clamp(ex, ey))
		self._action = 'expand'

	def _propose_outside_contract(self, reflect_value):
		# self._pending is currently the reflect point
		self._saved = (self._pending[:], reflect_value, self._evaluation_count)
		cx, cy = self._centroid()
		ox = cx + self._beta * (self._pending[0] - cx)
		oy = cy + self._beta * (self._pending[1] - cy)
		self._pending = list(self._clamp(ox, oy))
		self._action = 'outside_contract'

	def _propose_inside_contract(self):
		self._vertices.sort(key=lambda v: -v[2])
		cx, cy = self._centroid()
		wx, wy = self._vertices[2][0], self._vertices[2][1]
		ix = cx + self._beta * (wx - cx)
		iy = cy + self._beta * (wy - cy)
		self._pending = list(self._clamp(ix, iy))
		self._action = 'inside_contract'

	def _propose_shrink(self, vertex_idx):
		self._vertices.sort(key=lambda v: -v[2])
		bx, by = self._vertices[0][0], self._vertices[0][1]
		vx, vy = self._vertices[vertex_idx][0], self._vertices[vertex_idx][1]
		sx = bx + self._delta * (vx - bx)
		sy = by + self._delta * (vy - by)
		self._pending = list(self._clamp(sx, sy))
		self._action = f'shrink_{vertex_idx}'

	# ------------------------------------------------------------------
	# Utilities
	# ------------------------------------------------------------------

	def _replace_worst(self, value):
		self._vertices[2] = [
			self._pending[0], self._pending[1], value,
			self._evaluation_count,
		]

	def _centroid(self):
		"""Centroid of the two best vertices (assumes _vertices is sorted best-first)."""
		return (
			(self._vertices[0][0] + self._vertices[1][0]) / 2,
			(self._vertices[0][1] + self._vertices[1][1]) / 2,
		)

	def _clamp(self, x, y):
		return max(self._lb[0], x), max(self._lb[1], y)

	def _maybe_restart(self, center):
		if not self.tracking_enabled or len(self._vertices) != 3:
			return False

		# A small relative tolerance avoids immediately restarting a regular
		# simplex that was constructed at exactly the configured floor.
		if self.simplex_size < self._min_simplex_size * (1 - 1e-12):
			self._restart(center, reason='simplex_floor')
			return True
		if (
			self._max_vertex_age is not None
			and self.oldest_vertex_age >= self._max_vertex_age
		):
			self._restart(center, reason='vertex_age')
			return True
		return False

	def _restart(self, center, reason):
		angle = self._restart_count * self._restart_rotation
		self._seeds = []
		for idx in range(3):
			theta = angle + idx * 2 * math.pi / 3
			x = center[0] + self._min_simplex_size * math.cos(theta)
			y = center[1] + self._min_simplex_size * math.sin(theta)
			self._seeds.append(list(self._clamp(x, y)))

		self._vertices = []
		self._pending = None
		self._action = 'init'
		self._saved = None
		self._shrink_buf = None
		self._init_idx = 0
		self._restart_count += 1
		self._last_restart_reason = reason
		self._advance_init(None)

	def _limit_pending_step(self, origin):
		if (
			origin is None
			or self._max_proposal_step is None
			or self._restart_count == 0
		):
			return
		dx = self._pending[0] - origin[0]
		dy = self._pending[1] - origin[1]
		distance = math.hypot(dx, dy)
		if distance <= self._max_proposal_step:
			return
		scale = self._max_proposal_step / distance
		self._pending = list(self._clamp(
			origin[0] + dx * scale,
			origin[1] + dy * scale,
		))

	def _external_pending(self):
		return self._to_external(*self._pending)

	def _to_internal(self, x, y):
		if self._use_log_coordinates:
			return math.log(x), math.log(y)
		return x, y

	def _to_external(self, x, y):
		if self._use_log_coordinates:
			return math.exp(x), math.exp(y)
		return x, y
