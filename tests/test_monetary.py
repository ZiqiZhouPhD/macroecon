import math
import unittest

import macroABM


def make_monetary_economy(
	household_cash=5,
	firm_cash=5,
	goods_price=1,
	forbid_negative_cash=False,
):
	household = macroABM.HouseHold(
		'Household',
		macroABM.MonetaryHouseHoldLogic,
		initial_cash=household_cash,
		forbid_negative_cash=forbid_negative_cash,
	)
	firm = macroABM.Firm(
		'Firm',
		macroABM.MonetaryFirmLogic,
		initial_cash=firm_cash,
		forbid_negative_cash=forbid_negative_cash,
	)
	labor_market = macroABM.MoneyMarket(
		item='labor',
		seller=household,
		buyer=firm,
		price=1,
		volume=1,
	)
	goods_market = macroABM.MoneyMarket(
		item='consumption',
		seller=firm,
		buyer=household,
		price=goods_price,
		volume=1,
	)
	household.mount_relation('labor', labor_market)
	household.mount_relation('goods', goods_market)
	firm.mount_relation('labor', labor_market)
	firm.mount_relation('goods', goods_market)
	return household, firm, labor_market, goods_market


def enable_stepwise_pricing(firm):
	firm.logic.price_optimization_mode = 'stepwise'


class MoneyMarketTests(unittest.TestCase):
	def test_money_market_settlement_updates_goods_and_cash(self):
		household, firm, _, goods_market = make_monetary_economy()
		goods_market.price = 3
		goods_market.volume = 2

		goods_market.handle_transactions()

		self.assertEqual(household.step_consumption, 2)
		self.assertEqual(firm.step_product_sold, -2)
		self.assertEqual(household.cash, -1)
		self.assertEqual(firm.cash, 11)
		self.assertEqual(household.step_consumption_spending, 6)
		self.assertEqual(firm.step_sales_revenue, 6)

	def test_money_market_caps_volume_when_buyer_cannot_overdraft(self):
		household, firm, _, goods_market = make_monetary_economy(
			household_cash=5,
			firm_cash=0,
			forbid_negative_cash=True,
		)
		goods_market.price = 3
		goods_market.volume = 2

		goods_market.handle_transactions()

		self.assertAlmostEqual(goods_market.volume, 5 / 3)
		self.assertAlmostEqual(household.cash, 0)
		self.assertAlmostEqual(firm.cash, 5)
		self.assertAlmostEqual(household.step_consumption, 5 / 3)

	def test_agent_rejects_direct_negative_cash_when_forbidden(self):
		household, _, _, _ = make_monetary_economy(
			household_cash=5,
			forbid_negative_cash=True,
		)

		with self.assertRaises(ValueError):
			household.handle_transaction('money', -6)

	def test_labor_market_short_side_matching(self):
		_, _, labor_market, _ = make_monetary_economy()
		labor_market.supply_volume = 3
		labor_market.demand_volume = 2

		self.assertEqual(labor_market.match_short_side(), 2)

		labor_market.supply_volume = -1
		labor_market.demand_volume = 2

		self.assertEqual(labor_market.match_short_side(), 0)

	def test_commit_price_makes_current_price_available_as_previous_price(self):
		_, _, _, goods_market = make_monetary_economy()
		goods_market.price = 1.5

		goods_market.commit_price()

		self.assertEqual(goods_market.previous_price, 1.5)


class MonetaryBehaviorTests(unittest.TestCase):
	def test_household_uses_real_cash_not_nominal_cash_for_consumption(self):
		low_real_cash, _, labor_low, goods_low = make_monetary_economy(
			household_cash=10,
			goods_price=1,
		)
		high_nominal_same_real_cash, _, labor_high, goods_high = make_monetary_economy(
			household_cash=20,
			goods_price=2,
		)
		labor_high.price = 2

		low_real_cash.update_volumes()
		high_nominal_same_real_cash.update_volumes()

		self.assertAlmostEqual(
			labor_low.supply_volume,
			labor_high.supply_volume,
			places=12,
		)
		self.assertAlmostEqual(
			goods_low.demand_volume,
			goods_high.demand_volume,
			places=12,
		)

	def test_higher_real_cash_raises_household_desired_consumption(self):
		low_cash_household, _, _, low_cash_goods = make_monetary_economy(
			household_cash=2,
			goods_price=1,
		)
		high_cash_household, _, _, high_cash_goods = make_monetary_economy(
			household_cash=8,
			goods_price=1,
		)

		low_cash_household.update_volumes()
		high_cash_household.update_volumes()

		self.assertGreater(
			high_cash_goods.demand_volume,
			low_cash_goods.demand_volume,
		)

	def test_household_values_cash_at_current_goods_price(self):
		current_price_changed, _, changed_labor, changed_goods = make_monetary_economy(
			household_cash=10,
			goods_price=1,
		)
		equivalent_real_cash, _, baseline_labor, baseline_goods = make_monetary_economy(
			household_cash=5,
			goods_price=1,
		)
		# Preserve the same real wage while changing only this step's price and
		# leaving previous_price at its old value.
		changed_labor.price = 2
		changed_goods.price = 2

		current_price_changed.update_volumes()
		equivalent_real_cash.update_volumes()

		self.assertAlmostEqual(
			changed_goods.demand_volume,
			baseline_goods.demand_volume,
			places=12,
		)

	def test_higher_real_wage_raises_household_labor_supply(self):
		household, _, labor_market, goods_market = make_monetary_economy()
		goods_market.price = 1
		labor_market.price = 1
		household.update_volumes()
		baseline_labor = labor_market.supply_volume

		labor_market.price = 2
		household.update_volumes()

		self.assertGreater(labor_market.supply_volume, baseline_labor)

	def test_firm_uses_real_cash_not_nominal_cash_for_productivity(self):
		_, low_nominal_firm, _, _ = make_monetary_economy(
			firm_cash=10,
			goods_price=1,
		)
		_, high_nominal_same_real_firm, _, _ = make_monetary_economy(
			firm_cash=20,
			goods_price=2,
		)

		enable_stepwise_pricing(low_nominal_firm)
		enable_stepwise_pricing(high_nominal_same_real_firm)
		# Effective productivity is computed at the proposed current price.
		low_nominal_firm.update_prices()
		high_nominal_same_real_firm.update_prices()

		self.assertAlmostEqual(
			low_nominal_firm.logic.effective_productivity,
			high_nominal_same_real_firm.logic.effective_productivity,
			places=12,
		)

	def test_higher_real_firm_cash_raises_effective_productivity(self):
		_, low_cash_firm, _, _ = make_monetary_economy(
			firm_cash=1,
			goods_price=1,
		)
		_, high_cash_firm, _, _ = make_monetary_economy(
			firm_cash=10,
			goods_price=1,
		)

		enable_stepwise_pricing(low_cash_firm)
		enable_stepwise_pricing(high_cash_firm)
		low_cash_firm.update_prices()
		high_cash_firm.update_prices()

		self.assertGreater(
			high_cash_firm.logic.effective_productivity,
			low_cash_firm.logic.effective_productivity,
		)

	def test_firm_values_cash_at_candidate_current_goods_price(self):
		_, current_price_changed, changed_labor, changed_goods = make_monetary_economy(
			firm_cash=10,
			goods_price=1,
		)
		_, equivalent_real_cash, _, _ = make_monetary_economy(
			firm_cash=5,
			goods_price=1,
		)
		changed_labor.price = 2
		changed_goods.price = 2
		enable_stepwise_pricing(current_price_changed)
		enable_stepwise_pricing(equivalent_real_cash)

		current_price_changed.update_prices()
		equivalent_real_cash.update_prices()

		self.assertAlmostEqual(
			current_price_changed.logic.effective_productivity,
			equivalent_real_cash.logic.effective_productivity,
			places=12,
		)

	def test_productivity_liquidity_effect_is_bounded(self):
		_, firm, _, _ = make_monetary_economy(firm_cash=10_000)
		enable_stepwise_pricing(firm)

		firm.update_prices()

		self.assertGreaterEqual(
			firm.logic.effective_productivity,
			firm.logic.productivity * firm.logic.min_productivity_factor,
		)
		self.assertLessEqual(
			firm.logic.effective_productivity,
			firm.logic.productivity * firm.logic.max_productivity_factor,
		)
		self.assertTrue(math.isfinite(firm.logic.effective_productivity))


class FirmPricingTests(unittest.TestCase):
	def test_instantaneous_frozen_state_solve_is_the_default(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
		initial_cash = firm.cash
		firm.update_prices()

		self.assertEqual(firm.logic.price_optimization_mode, 'instantaneous')
		self.assertIsNone(firm.logic._nm)
		self.assertTrue(firm.logic.nm_last_converged)
		self.assertGreater(firm.logic.nm_last_evaluations, 3)
		self.assertEqual(firm.cash, initial_cash)
		self.assertGreater(labor_market.price, 0)
		self.assertGreater(goods_market.price, 0)

	def test_firm_maximizes_expected_real_profit_under_clearing(self):
		household, firm, labor_market, goods_market = make_monetary_economy(
			household_cash=2.9809704670852475,
			firm_cash=7.019029532914724,
			goods_price=0.237348,
		)
		labor_market.price = 0.052028
		household.logic.real_wage_0 = 1
		firm.update_prices()

		self.assertTrue(firm.logic.nm_last_converged)
		outcome = firm.logic._evaluate_candidate(
			labor_market.price,
			goods_market.price,
		)
		real_wage = labor_market.price / goods_market.price
		self.assertAlmostEqual(outcome[1], outcome[2], places=7)
		self.assertAlmostEqual(
			firm.logic.nm_last_predicted_profit,
			outcome[2] - real_wage * outcome[0],
			places=12,
		)
		self.assertAlmostEqual(
			outcome[5] / goods_market.price,
			firm.logic.nm_last_predicted_profit,
			places=7,
		)

	def test_expected_real_profit_does_not_subtract_realized_demand(self):
		_, low_demand_firm, _, _ = make_monetary_economy(
			household_cash=1,
			firm_cash=5,
		)
		_, high_demand_firm, _, _ = make_monetary_economy(
			household_cash=9,
			firm_cash=5,
		)
		low_demand_firm.logic._initialize_household_real_wage_reference()
		high_demand_firm.logic._initialize_household_real_wage_reference()

		low_outcome = low_demand_firm.logic._evaluate_candidate(0.5, 1)
		high_outcome = high_demand_firm.logic._evaluate_candidate(0.5, 1)

		self.assertNotAlmostEqual(low_outcome[3], high_outcome[3])
		self.assertAlmostEqual(low_outcome[4], high_outcome[4], places=12)

	def test_followup_solve_tracks_real_profit_optimum_without_price_jump(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
		firm.update_prices()
		first_prices = labor_market.price, goods_market.price

		firm.update_prices()

		self.assertEqual(
			firm.logic.price_solver_last_method,
			'expected_clearing_foc',
		)
		self.assertAlmostEqual(labor_market.price, first_prices[0], places=8)
		self.assertAlmostEqual(goods_market.price, first_prices[1], places=8)

	def test_low_household_cash_still_has_finite_real_profit_optimum(self):
		_, firm, labor_market, goods_market = make_monetary_economy(
			household_cash=0.01,
			firm_cash=9.99,
		)

		firm.update_prices()

		self.assertTrue(firm.logic.nm_last_converged)
		self.assertTrue(math.isfinite(labor_market.price))
		self.assertTrue(math.isfinite(goods_market.price))
		self.assertGreater(firm.logic.nm_last_predicted_profit, 0)

	def test_stepwise_compatibility_mode_enables_tracking_safeguards(self):
		_, firm, _, _ = make_monetary_economy()
		enable_stepwise_pricing(firm)
		firm.update_prices()
		self.assertTrue(firm.logic._nm.tracking_enabled)
		self.assertAlmostEqual(firm.logic.nm_initial_log_size, 1e-3)
		self.assertAlmostEqual(firm.logic.nm_min_log_size, 3e-5)
		self.assertEqual(firm.logic.nm_max_vertex_age, 20)
		self.assertAlmostEqual(firm.logic.nm_max_log_step, 1e-3)
		self.assertTrue(firm.logic._nm._use_log_coordinates)

	def test_nm_uses_small_seed_prices_for_first_three_steps(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
		enable_stepwise_pricing(firm)
		w0, p0 = labor_market.price, goods_market.price
		seed_scale = math.exp(firm.logic.nm_initial_log_size)

		firm.update_prices()  # step 0
		self.assertAlmostEqual(labor_market.price, w0)
		self.assertAlmostEqual(goods_market.price, p0)

		firm.logic.record_profit(0)
		firm.update_prices()  # step 1 — scaled wage seed
		self.assertAlmostEqual(labor_market.price, w0 * seed_scale)
		self.assertAlmostEqual(goods_market.price, p0)

		firm.logic.record_profit(0)
		firm.update_prices()  # step 2 — scaled price seed
		self.assertAlmostEqual(labor_market.price, w0)
		self.assertAlmostEqual(goods_market.price, p0 * seed_scale)

	def test_nm_transitions_to_reflect_phase_after_step_3(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
		enable_stepwise_pricing(firm)
		for _ in range(3):
			firm.update_prices()
			firm.logic.record_profit(0)
		# Step 3 finalizes the simplex and proposes the first reflected point.
		firm.update_prices()
		self.assertEqual(firm.logic._nm._action, 'reflect')
		self.assertIsNotNone(firm.logic._nm._pending)

	def test_nm_accepts_improved_reflection(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
		enable_stepwise_pricing(firm)
		# Give seeds distinct profits so best=10, second=5, worst=0.
		firm.update_prices()
		firm.logic.record_profit(10)
		firm.update_prices()
		firm.logic.record_profit(5)
		firm.update_prices()
		firm.logic.record_profit(0)
		firm.update_prices()  # step 3: proposes first reflection
		# A value between second(5) and best(10) is accepted directly without expand.
		firm.logic.record_profit(7)
		firm.update_prices()  # step 4: should accept and re-enter reflect
		self.assertEqual(firm.logic._nm._action, 'reflect')

	def test_instantaneous_prices_are_always_positive(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
		for i in range(10):
			firm.update_prices()
			firm.logic.record_profit(float(i % 3))
			self.assertGreater(labor_market.price, 0)
			self.assertGreater(goods_market.price, 0)


class MonetarySimulationTests(unittest.TestCase):
	def _run_one_monetary_step(self, household, firm, labor_market, goods_market):
		for agent in [household, firm]:
			agent.step_preprocess()
		for agent in [household, firm]:
			agent.update_prices()
		for agent in [household, firm]:
			agent.update_volumes()

		# Full labor absorption — no rationing.
		labor_market.volume = labor_market.supply_volume
		labor_market.handle_transactions()

		firm.step_production = firm.step_labor * firm.step_effective_productivity

		# Demand-determined goods market.
		goods_market.volume = min(goods_market.demand_volume, firm.step_production)
		goods_market.handle_transactions()

		goods_profit = firm.step_production - goods_market.volume
		firm.step_goods_imbalance = goods_profit
		firm.step_profit_goods = goods_profit
		real_profit = (
			firm.step_production
			- labor_market.price / goods_market.price * firm.step_labor
		)
		firm.step_real_profit = real_profit
		firm.logic.record_profit(real_profit)

		for market in [labor_market, goods_market]:
			market.commit_price()

	def _run_monetary_horizon(self, dt, total_time=0.1):
		household, firm, labor_market, goods_market = make_monetary_economy(
			forbid_negative_cash=True,
		)
		for _ in range(round(total_time / dt)):
			for agent in [household, firm]:
				agent.step_preprocess()
			for agent in [household, firm]:
				agent.update_prices()
			for agent in [household, firm]:
				agent.update_volumes()

			labor_market.volume = labor_market.supply_volume * dt
			labor_market.handle_transactions()
			firm.step_production = (
				firm.step_labor * firm.step_effective_productivity
			)
			goods_market.volume = min(
				goods_market.demand_volume * dt,
				firm.step_production,
			)
			goods_market.handle_transactions()
			real_profit_rate = (
				firm.step_production
				- labor_market.price / goods_market.price * firm.step_labor
			) / dt
			firm.logic.record_profit(real_profit_rate)

			if firm.cash > 1e-9 and household.cash > 1e-9:
				dividend = 0.1 * dt * math.log(firm.cash / household.cash)
				dividend = min(dividend, firm.cash)
				dividend = max(dividend, -household.cash)
				firm.cash -= dividend
				household.cash += dividend

			labor_market.commit_price()
			goods_market.commit_price()

		return (
			labor_market.price,
			goods_market.price,
			household.cash,
			firm.cash,
		)

	def test_one_monetary_step_conserves_total_cash(self):
		household, firm, labor_market, goods_market = make_monetary_economy()
		initial_total_cash = household.cash + firm.cash

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		self.assertAlmostEqual(household.cash + firm.cash, initial_total_cash)

	def test_household_consumption_does_not_exceed_production(self):
		household, firm, labor_market, goods_market = make_monetary_economy()

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		self.assertLessEqual(goods_market.volume, firm.step_production + 1e-12)

	def test_goods_imbalance_is_nonnegative(self):
		household, firm, labor_market, goods_market = make_monetary_economy()

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		self.assertGreaterEqual(firm.step_goods_imbalance, 0)

	def test_firm_absorbs_all_household_labor_supply(self):
		household, firm, labor_market, goods_market = make_monetary_economy()

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		self.assertAlmostEqual(labor_market.volume, labor_market.supply_volume)

	def test_frozen_objective_matches_realized_real_operating_profit(self):
		household, firm, labor_market, goods_market = make_monetary_economy()

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		realized_real_profit = (
			firm.step_production
			- labor_market.price / goods_market.price * firm.step_labor
		)
		self.assertAlmostEqual(
			realized_real_profit,
			firm.logic.nm_last_predicted_profit,
			places=12,
		)
		self.assertAlmostEqual(firm.step_goods_imbalance, 0, places=7)

	def test_time_refinement_converges(self):
		coarse = self._run_monetary_horizon(0.002)
		medium = self._run_monetary_horizon(0.001)
		fine = self._run_monetary_horizon(0.0005)
		reference = self._run_monetary_horizon(0.00025)
		coarse_error = sum(abs(x - y) for x, y in zip(coarse, reference))
		medium_error = sum(abs(x - y) for x, y in zip(medium, reference))
		fine_error = sum(abs(x - y) for x, y in zip(fine, reference))

		self.assertLessEqual(medium_error, coarse_error)
		self.assertLessEqual(fine_error, medium_error)
		self.assertLess(fine_error, 1e-3)


if __name__ == '__main__':
	unittest.main()
