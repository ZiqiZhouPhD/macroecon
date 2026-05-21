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

		# Effective productivity is computed in update_prices().
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

		low_cash_firm.update_prices()
		high_cash_firm.update_prices()

		self.assertGreater(
			high_cash_firm.logic.effective_productivity,
			low_cash_firm.logic.effective_productivity,
		)

	def test_productivity_liquidity_effect_is_bounded(self):
		_, firm, _, _ = make_monetary_economy(firm_cash=10_000)

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


class NelderMeadPricingTests(unittest.TestCase):
	def test_nm_uses_seed_prices_for_first_three_steps(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
		w0, p0 = labor_market.price, goods_market.price

		firm.update_prices()  # step 0
		self.assertAlmostEqual(labor_market.price, w0)
		self.assertAlmostEqual(goods_market.price, p0)

		firm.logic.record_profit(0)
		firm.update_prices()  # step 1 — scaled wage seed
		self.assertAlmostEqual(labor_market.price, w0 * 1.2)
		self.assertAlmostEqual(goods_market.price, p0)

		firm.logic.record_profit(0)
		firm.update_prices()  # step 2 — scaled price seed
		self.assertAlmostEqual(labor_market.price, w0)
		self.assertAlmostEqual(goods_market.price, p0 * 1.2)

	def test_nm_transitions_to_reflect_phase_after_step_3(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
		for _ in range(3):
			firm.update_prices()
			firm.logic.record_profit(0)
		# Step 3 finalizes the simplex and proposes the first reflected point.
		firm.update_prices()
		self.assertEqual(firm.logic._nm._action, 'reflect')
		self.assertIsNotNone(firm.logic._nm._pending)

	def test_nm_accepts_improved_reflection(self):
		_, firm, labor_market, goods_market = make_monetary_economy()
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

	def test_nm_prices_are_always_positive(self):
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
		firm.step_profit_goods = goods_profit
		firm.logic.record_profit(goods_profit)

		for market in [labor_market, goods_market]:
			market.commit_price()

	def test_one_monetary_step_conserves_total_cash(self):
		household, firm, labor_market, goods_market = make_monetary_economy()
		initial_total_cash = household.cash + firm.cash

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		self.assertAlmostEqual(household.cash + firm.cash, initial_total_cash)

	def test_household_consumption_does_not_exceed_production(self):
		household, firm, labor_market, goods_market = make_monetary_economy()

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		self.assertLessEqual(goods_market.volume, firm.step_production + 1e-12)

	def test_goods_profit_is_nonnegative(self):
		household, firm, labor_market, goods_market = make_monetary_economy()

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		self.assertGreaterEqual(firm.step_profit_goods, 0)

	def test_firm_absorbs_all_household_labor_supply(self):
		household, firm, labor_market, goods_market = make_monetary_economy()

		self._run_one_monetary_step(household, firm, labor_market, goods_market)

		self.assertAlmostEqual(labor_market.volume, labor_market.supply_volume)


if __name__ == '__main__':
	unittest.main()
