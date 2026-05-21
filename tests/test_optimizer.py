import unittest

from macroABM.optimizer import StepwiseNelderMead2D


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEEDS = [(1.0, 1.0), (2.0, 1.0), (1.0, 2.0)]


def _make_nm(seeds=None, lower_bounds=(0.0, 0.0)):
	seeds = seeds or SEEDS
	return StepwiseNelderMead2D(seeds=seeds, lower_bounds=lower_bounds)


def _run_init(nm, values=(10, 5, 1)):
	"""Advance past the 3-seed initialisation phase.

	Returns the reflect point proposed after init (the 4th advance return
	value). After this call nm._action == 'reflect'.

	Simplex vertex layout with SEEDS and values=(10, 5, 1):
	  (1,1,10)  best
	  (2,1, 5)  second
	  (1,2, 1)  worst
	Centroid of best two: (1.5, 1.0)
	Reflect of worst:     (2.0, 0.0)   <- returned / pending after init
	"""
	nm.advance(None)
	for v in values:
		nm.advance(v)
	# nm._action == 'reflect', nm._pending == [2.0, 0.0]


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class InitialisationTests(unittest.TestCase):
	def test_first_call_proposes_first_seed(self):
		nm = _make_nm()
		pt = nm.advance(None)
		self.assertAlmostEqual(pt[0], 1.0)
		self.assertAlmostEqual(pt[1], 1.0)

	def test_second_call_proposes_second_seed(self):
		nm = _make_nm()
		nm.advance(None)
		pt = nm.advance(0)
		self.assertAlmostEqual(pt[0], 2.0)
		self.assertAlmostEqual(pt[1], 1.0)

	def test_third_call_proposes_third_seed(self):
		nm = _make_nm()
		nm.advance(None)
		nm.advance(0)
		pt = nm.advance(0)
		self.assertAlmostEqual(pt[0], 1.0)
		self.assertAlmostEqual(pt[1], 2.0)

	def test_fourth_call_enters_reflect_phase(self):
		nm = _make_nm()
		_run_init(nm)
		self.assertEqual(nm._action, 'reflect')

	def test_reflect_point_after_init_is_away_from_worst(self):
		# With values (10,5,1): worst=(1,2), centroid=(1.5,1.0), reflect=(2.0,0.0)
		nm = _make_nm()
		_run_init(nm, values=(10, 5, 1))
		self.assertAlmostEqual(nm._pending[0], 2.0)
		self.assertAlmostEqual(nm._pending[1], 0.0)

	def test_best_property_returns_highest_value_vertex(self):
		nm = _make_nm()
		_run_init(nm, values=(10, 5, 1))
		b = nm.best
		self.assertAlmostEqual(b[2], 10)
		self.assertAlmostEqual(b[0], 1.0)
		self.assertAlmostEqual(b[1], 1.0)

	def test_rejects_wrong_seed_count(self):
		with self.assertRaises(ValueError):
			StepwiseNelderMead2D(seeds=[(0, 0), (1, 1)])


# ---------------------------------------------------------------------------
# Reflect: the four decision branches
# ---------------------------------------------------------------------------

class ReflectBranchTests(unittest.TestCase):
	"""
	After _run_init with values=(10,5,1):
	  best=10, second=5, worst=1
	  pending (reflect point) = (2.0, 0.0)
	"""

	def setUp(self):
		self.nm = _make_nm()
		_run_init(self.nm)

	def test_reflect_accepted_when_better_than_second(self):
		# value=7: second(5) < 7 <= best(10) -> accept reflect, stay in reflect phase
		self.nm.advance(7)
		self.assertEqual(self.nm._action, 'reflect')
		# Worst vertex replaced with reflect point (2.0, 0.0, 7)
		vals = [v[2] for v in self.nm._vertices]
		self.assertIn(7, vals)

	def test_expand_proposed_when_reflect_better_than_best(self):
		# value=15 > best=10 -> expansion proposed
		self.nm.advance(15)
		self.assertEqual(self.nm._action, 'expand')

	def test_expand_point_is_further_than_reflect(self):
		# Reflect was at x=2.0; expand (gamma=2) from centroid(1.5,1.0) goes to x=2.5
		self.nm.advance(15)
		self.assertAlmostEqual(self.nm._pending[0], 2.5)
		self.assertAlmostEqual(self.nm._pending[1], 0.0)   # clamped from -1.0

	def test_outside_contract_proposed_when_reflect_between_worst_and_second(self):
		# value=3: worst(1) < 3 <= second(5) -> outside contract
		self.nm.advance(3)
		self.assertEqual(self.nm._action, 'outside_contract')

	def test_outside_contract_point_between_centroid_and_reflect(self):
		# centroid=(1.5,1.0), reflect=(2.0,0.0), oc = midpoint = (1.75, 0.5)
		self.nm.advance(3)
		self.assertAlmostEqual(self.nm._pending[0], 1.75)
		self.assertAlmostEqual(self.nm._pending[1], 0.5)

	def test_inside_contract_proposed_when_reflect_worse_than_worst(self):
		# value=0 <= worst=1 -> inside contract
		self.nm.advance(0)
		self.assertEqual(self.nm._action, 'inside_contract')

	def test_inside_contract_point_between_centroid_and_worst(self):
		# centroid=(1.5,1.0), worst=(1,2), ic = midpoint = (1.25, 1.5)
		self.nm.advance(0)
		self.assertAlmostEqual(self.nm._pending[0], 1.25)
		self.assertAlmostEqual(self.nm._pending[1], 1.5)


# ---------------------------------------------------------------------------
# Expand
# ---------------------------------------------------------------------------

class ExpandTests(unittest.TestCase):
	def setUp(self):
		self.nm = _make_nm()
		_run_init(self.nm)
		self.nm.advance(15)   # triggers expand; pending=(2.5, 0.0), saved=([2.0,0.0],15)

	def test_expand_accepted_when_better_than_reflect(self):
		# expand value=20 > reflect=15 -> accept expand, return to reflect
		self.nm.advance(20)
		self.assertEqual(self.nm._action, 'reflect')
		vals = [v[2] for v in self.nm._vertices]
		self.assertIn(20, vals)

	def test_expand_accepted_vertex_is_expand_point(self):
		self.nm.advance(20)
		best = self.nm.best
		self.assertAlmostEqual(best[2], 20)
		self.assertAlmostEqual(best[0], 2.5)

	def test_expand_rejected_when_reflect_is_better(self):
		# expand value=12 < reflect=15 -> reject expand, accept reflect point
		self.nm.advance(12)
		self.assertEqual(self.nm._action, 'reflect')
		vals = [v[2] for v in self.nm._vertices]
		self.assertIn(15, vals)   # reflect accepted
		self.assertNotIn(12, vals)

	def test_expand_rejected_vertex_is_reflect_point(self):
		self.nm.advance(12)
		best = self.nm.best
		self.assertAlmostEqual(best[2], 15)
		self.assertAlmostEqual(best[0], 2.0)  # reflect x-coord


# ---------------------------------------------------------------------------
# Outside contraction
# ---------------------------------------------------------------------------

class OutsideContractTests(unittest.TestCase):
	def setUp(self):
		self.nm = _make_nm()
		_run_init(self.nm)
		self.nm.advance(3)   # triggers outside contract; pending=(1.75,0.5), saved=([2.0,0.0],3)

	def test_outside_contract_accepted_when_at_least_as_good_as_reflect(self):
		# oc value=4 >= reflect=3 -> accept, back to reflect
		self.nm.advance(4)
		self.assertEqual(self.nm._action, 'reflect')
		vals = [v[2] for v in self.nm._vertices]
		self.assertIn(4, vals)

	def test_outside_contract_rejected_triggers_shrink(self):
		# oc value=2 < reflect=3 -> shrink
		self.nm.advance(2)
		self.assertEqual(self.nm._action, 'shrink_1')


# ---------------------------------------------------------------------------
# Inside contraction
# ---------------------------------------------------------------------------

class InsideContractTests(unittest.TestCase):
	def setUp(self):
		self.nm = _make_nm()
		_run_init(self.nm)
		self.nm.advance(0)   # triggers inside contract; pending=(1.25,1.5)

	def test_inside_contract_accepted_when_better_than_worst(self):
		# ic value=2 > worst=1 -> accept, back to reflect
		self.nm.advance(2)
		self.assertEqual(self.nm._action, 'reflect')
		vals = [v[2] for v in self.nm._vertices]
		self.assertIn(2, vals)

	def test_inside_contract_rejected_triggers_shrink(self):
		# ic value=0 <= worst=1 -> shrink
		self.nm.advance(0)
		self.assertEqual(self.nm._action, 'shrink_1')

	def test_shrink_step1_point(self):
		# shrink vertex 1=(2,1) toward best=(1,1): midpoint=(1.5, 1.0)
		self.nm.advance(0)
		self.assertAlmostEqual(self.nm._pending[0], 1.5)
		self.assertAlmostEqual(self.nm._pending[1], 1.0)


# ---------------------------------------------------------------------------
# Shrink (two-step)
# ---------------------------------------------------------------------------

class ShrinkTests(unittest.TestCase):
	def _reach_shrink(self):
		nm = _make_nm()
		_run_init(nm)
		nm.advance(0)   # inside contract
		nm.advance(0)   # inside contract fails -> shrink_1
		return nm

	def test_shrink_1_proposes_midpoint_of_best_and_second(self):
		# best=(1,1), second=(2,1): midpoint=(1.5,1.0)
		nm = self._reach_shrink()
		self.assertAlmostEqual(nm._pending[0], 1.5)
		self.assertAlmostEqual(nm._pending[1], 1.0)

	def test_shrink_2_proposes_midpoint_of_best_and_worst(self):
		# After shrink_1, advance to shrink_2
		# best=(1,1), worst=(1,2): midpoint=(1.0,1.5)
		nm = self._reach_shrink()
		nm.advance(0.5)   # shrink_1 result
		self.assertEqual(nm._action, 'shrink_2')
		self.assertAlmostEqual(nm._pending[0], 1.0)
		self.assertAlmostEqual(nm._pending[1], 1.5)

	def test_shrink_completes_and_returns_to_reflect(self):
		nm = self._reach_shrink()
		nm.advance(0.5)   # shrink_1
		nm.advance(0.5)   # shrink_2
		self.assertEqual(nm._action, 'reflect')

	def test_shrink_applies_both_vertices(self):
		nm = self._reach_shrink()
		nm.advance(0.5)   # shrink_1: vertex 1 <- [1.5, 1.0, 0.5]
		nm.advance(0.3)   # shrink_2: vertex 2 <- [1.0, 1.5, 0.3]
		coords = [(v[0], v[1]) for v in nm._vertices]
		self.assertIn((1.5, 1.0), coords)
		self.assertIn((1.0, 1.5), coords)


# ---------------------------------------------------------------------------
# Lower-bound enforcement
# ---------------------------------------------------------------------------

class LowerBoundTests(unittest.TestCase):
	def test_all_proposed_points_respect_lower_bounds(self):
		lb = (0.5, 0.8)
		nm = StepwiseNelderMead2D(
			seeds=[(1.0, 1.0), (2.0, 1.0), (1.0, 2.0)],
			lower_bounds=lb,
		)
		pt = nm.advance(None)
		for i in range(60):
			self.assertGreaterEqual(pt[0], lb[0], f'x below lower bound at step {i}')
			self.assertGreaterEqual(pt[1], lb[1], f'y below lower bound at step {i}')
			pt = nm.advance(float(i % 7))

	def test_seed_below_lower_bound_is_clamped(self):
		nm = StepwiseNelderMead2D(
			seeds=[(0.1, 0.1), (1.0, 0.1), (0.1, 1.0)],
			lower_bounds=(0.5, 0.5),
		)
		pt = nm.advance(None)
		self.assertAlmostEqual(pt[0], 0.5)
		self.assertAlmostEqual(pt[1], 0.5)


# ---------------------------------------------------------------------------
# Convergence on a known landscape
# ---------------------------------------------------------------------------

class ConvergenceTests(unittest.TestCase):
	def test_converges_to_quadratic_maximum(self):
		w_star, p_star = 2.0, 3.0

		def f(w, p):
			return -(w - w_star) ** 2 - (p - p_star) ** 2

		nm = StepwiseNelderMead2D(
			seeds=[(0.5, 1.0), (1.5, 1.0), (0.5, 2.0)],
			lower_bounds=(0.0, 0.0),
		)

		pt = nm.advance(None)
		for _ in range(500):
			pt = nm.advance(f(*pt))

		best = nm.best
		self.assertAlmostEqual(best[0], w_star, places=1)
		self.assertAlmostEqual(best[1], p_star, places=1)

	def test_best_value_improves_over_seeds(self):
		def f(w, p):
			return -(w - 5.0) ** 2 - (p - 5.0) ** 2

		seeds = [(1.0, 1.0), (2.0, 1.0), (1.0, 2.0)]
		seed_values = [f(*s) for s in seeds]

		nm = StepwiseNelderMead2D(seeds=seeds, lower_bounds=(0.0, 0.0))
		pt = nm.advance(None)
		for _ in range(100):
			pt = nm.advance(f(*pt))

		self.assertGreater(nm.best[2], max(seed_values))


if __name__ == '__main__':
	unittest.main()
