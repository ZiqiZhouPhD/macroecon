import math
import unittest

import macroABM


class BarterEconomyTests(unittest.TestCase):
	def test_barter_market_price_and_transactions(self):
		household = macroABM.HouseHold('Household', macroABM.LinearHouseHoldLogic)
		firm = macroABM.Firm('Firm', macroABM.LinearFirmLogic)
		market = macroABM.BarterMarket(
			items=('labor', 'consumption'),
			agents=(household, firm),
			volumes=[2, 4],
		)

		market.handle_transactions()

		self.assertEqual(market.price, 0.5)
		self.assertEqual(household.step_labor, -2)
		self.assertEqual(household.step_consumption, 4)
		self.assertEqual(firm.step_labor, 2)
		self.assertEqual(firm.step_product_sold, -4)

	def test_barter_household_labor_supply_rises_when_consumption_gets_cheaper(self):
		household = macroABM.HouseHold('Household', macroABM.LinearHouseHoldLogic)
		firm = macroABM.Firm('Firm', macroABM.LinearFirmLogic)
		market = macroABM.BarterMarket(
			items=('labor', 'consumption'),
			agents=(household, firm),
			volumes=[1, 1],
		)
		household.mount_relation('labor_consumption', market)

		market.price = 1
		household.update_volumes()
		baseline_labor = market.volumes[0]
		baseline_consumption = market.volumes[1]

		market.price = 0.5
		household.update_volumes()

		self.assertGreater(market.volumes[0], baseline_labor)
		self.assertGreater(market.volumes[1], baseline_consumption)
		self.assertTrue(math.isfinite(market.volumes[0]))
		self.assertTrue(math.isfinite(market.volumes[1]))

	def test_existing_agents_do_not_need_initial_cash(self):
		household = macroABM.HouseHold('Household', macroABM.LinearHouseHoldLogic)
		firm = macroABM.Firm('Firm', macroABM.LinearFirmLogic)

		self.assertEqual(household.cash, 0)
		self.assertEqual(firm.cash, 0)


if __name__ == '__main__':
	unittest.main()
