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
	"""

	def __init__(self, seeds, lower_bounds=(0.0, 0.0),
				 alpha=1.0, gamma=2.0, beta=0.5, delta=0.5):
		if len(seeds) != 3:
			raise ValueError('exactly 3 seed points are required for a 2-D simplex')
		self._seeds = [list(s) for s in seeds]
		self._lb = lower_bounds
		self._alpha = alpha
		self._gamma = gamma
		self._beta = beta
		self._delta = delta

		self._vertices = []       # [x, y, value] triples
		self._pending = None      # [x, y] most recently proposed point
		self._action = 'init'
		self._saved = None        # ([x, y], value) stashed for expand / outside-contract
		self._shrink_buf = None   # first shrunk vertex held during two-step shrink
		self._init_idx = 0        # next seed index to propose (0–2 during init)

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------

	def advance(self, observed_value):
		"""
		Feed the objective value observed at the last proposed point, update
		the simplex, and return the next (x, y) point to evaluate.
		Pass None on the very first call.
		"""
		if self._action == 'init':
			return self._advance_init(observed_value)
		if observed_value is not None:
			self._process(observed_value)
		return tuple(self._pending)

	@property
	def best(self):
		"""Best [x, y, value] triple seen so far, or None before init completes."""
		if not self._vertices:
			return None
		return max(self._vertices, key=lambda v: v[2])

	# ------------------------------------------------------------------
	# Initialisation phase
	# ------------------------------------------------------------------

	def _advance_init(self, observed_value):
		if self._init_idx == 0:
			x, y = self._clamp(*self._seeds[0])
			self._pending = [x, y]
			self._init_idx = 1
			return (x, y)

		self._vertices.append([self._pending[0], self._pending[1], observed_value])

		if self._init_idx < 3:
			x, y = self._clamp(*self._seeds[self._init_idx])
			self._pending = [x, y]
			self._init_idx += 1
			return (x, y)

		# All three seeds evaluated; enter running phase.
		self._action = 'reflect'
		self._propose_reflect()
		return tuple(self._pending)

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
			r_pt, r_val = self._saved
			if value > r_val:
				self._replace_worst(value)
			else:
				self._vertices[2] = [r_pt[0], r_pt[1], r_val]
			self._propose_reflect()

		elif self._action == 'outside_contract':
			_, r_val = self._saved
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
			self._shrink_buf = [self._pending[0], self._pending[1], value]
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
		self._saved = (self._pending[:], reflect_value)
		cx, cy = self._centroid()
		ex = cx + self._gamma * (self._pending[0] - cx)
		ey = cy + self._gamma * (self._pending[1] - cy)
		self._pending = list(self._clamp(ex, ey))
		self._action = 'expand'

	def _propose_outside_contract(self, reflect_value):
		# self._pending is currently the reflect point
		self._saved = (self._pending[:], reflect_value)
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
		self._vertices[2] = [self._pending[0], self._pending[1], value]

	def _centroid(self):
		"""Centroid of the two best vertices (assumes _vertices is sorted best-first)."""
		return (
			(self._vertices[0][0] + self._vertices[1][0]) / 2,
			(self._vertices[0][1] + self._vertices[1][1]) / 2,
		)

	def _clamp(self, x, y):
		return max(self._lb[0], x), max(self._lb[1], y)
