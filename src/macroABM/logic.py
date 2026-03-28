from . import functions

class Logic:
	def __init__(self, owner):
		self.owner = owner

	def update_prices(self):
		pass

	def update_volumes(self):
		pass

class HouseHoldLogic(Logic):
	def __init__(self, household):
		self.household = household

	def get_utility(self, labor, consumption):
		pass

	def update_volumes(self):
		# At given consumption price, labor price, and savings
		# Compute the labor and consumption with optimal utility
		# u = u_l(l) + u_c((l * p_l + s) / p_c)
		pass

class LinearHouseHoldLogic(HouseHoldLogic):
	def __init__(self, household):
		self.household = household
		self.elasticity = 0.2 # labor increase % / wage increase %
		self.labor_0 = None
		self.consumption_0 = None
		self.price_0 = None

	def init_market_data(self, labor_0, consumption_0):
		self.labor_0 = labor_0
		self.consumption_0 = consumption_0
		self.price_0 = labor_0 / consumption_0

	def update_volumes(self):
		if self.price_0 is None:
			self.init_market_data(
				self.household.relations['labor_consumption'].volumes[0],
				self.household.relations['labor_consumption'].volumes[1]
			)
		price = self.household.relations['labor_consumption'].price
		labor_volume = self.labor_0 * (price / self.price_0) ** (-self.elasticity)
		consumption_volume = labor_volume / price
		self.household.relations['labor_consumption'].volumes[0] = labor_volume
		self.household.relations['labor_consumption'].volumes[1] = consumption_volume

# class LinearHouseHoldLogic(Logic):
# 	def __init__(self, household):
# 		self.household = household
# 		self.margin_utility_of_labor = functions.LinearFunction(0, -1)
# 		self.margin_utility_of_consumption = functions.LinearFunction(2, -1)

# 	def update_volumes(self):
# 		price = self.household.relations['labor'].price / self.household.relations['consumption'].price
# 		savings_consumption = self.household.savings / self.household.relations['consumption'].price
# 		labor_volume = - (self.margin_utility_of_labor.intercept + price * self.margin_utility_of_consumption.slope * savings_consumption + price * self.margin_utility_of_consumption.intercept) / (self.margin_utility_of_labor.slope + price * price * self.margin_utility_of_consumption.slope)
# 		consumption_volume = (labor_volume * price) + savings_consumption
# 		print(self.margin_utility_of_labor.evaluate(labor_volume) + price * self.margin_utility_of_consumption.evaluate(consumption_volume)) # should be 0
# 		self.household.relations['labor'].volume += labor_volume
# 		self.household.relations['consumption'].volume += consumption_volume

# 	def get_micro_price_elasticity_of_consumption(self):
# 		price = self.household.relations['labor'].price / self.household.relations['consumption'].price
# 		savings_consumption = self.household.savings / self.household.relations['consumption'].price
# 		labor_volume = - (self.margin_utility_of_labor.intercept + price * self.margin_utility_of_consumption.slope * savings_consumption + price * self.margin_utility_of_consumption.intercept) / (self.margin_utility_of_labor.slope + price * price * self.margin_utility_of_consumption.slope)
# 		consumption_volume = (labor_volume * price) + savings_consumption
# 		numerator = - price * (self.margin_utility_of_labor.slope + price * price * self.margin_utility_of_consumption.slope) + (self.margin_utility_of_labor.intercept + price * self.margin_utility_of_consumption.slope * savings_consumption + price * self.margin_utility_of_consumption.intercept) * (2 * price * self.margin_utility_of_consumption.slope)
# 		denominator = (self.margin_utility_of_labor.slope + price * price * self.margin_utility_of_consumption.slope) ** 2
# 		dl_dp = numerator / denominator
# 		dc_dp = dl_dp * price + labor_volume * (- price / self.household.relations['consumption'].price)
# 		elasticity = (dc_dp * self.household.relations['consumption'].price) / consumption_volume
# 		competition_factor = 5
# 		return elasticity * competition_factor

class FirmLogic(Logic):
	def __init__(self, firm):
		self.firm = firm

	def get_utility(self, labor, consumption, investment):
		pass

	def update_prices(self):
		pass

class LinearFirmLogic(FirmLogic):
	def __init__(self, firm):
		self.firm = firm
		self.productivity = 2
		self.market_elasticity = -3 # Microscopic consumption change / price change

	def get_utility(self, labor, consumption_price_of_labor):
		production = self.productivity * labor
		consumption = consumption_price_of_labor * labor
		return production - consumption

	def update_prices(self):
		# Newton's method
		price = self.firm.relations['labor_consumption'].price
		numerator = (self.productivity * price - 1) * self.market_elasticity + 1
		denominator = ((self.productivity * price - 1) * self.market_elasticity + 2) * (self.market_elasticity - 1)
		if abs(denominator) < 1e-6:
			self.firm.relations['labor_consumption'].price *= 1.1
			return
		if denominator > 0: # Unstable, move away
			denominator = - denominator
		self.firm.relations['labor_consumption'].price -= price * numerator / denominator
