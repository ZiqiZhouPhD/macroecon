class Agent:
	def __init__(self, name, logic_constructor, forbid_negative_cash=False):
		self.name = name
		self.forbid_negative_cash = forbid_negative_cash
		self.logic = logic_constructor(self)
		self.relations = dict()

	def mount_relation(self, relation_name, relation):
		self.relations[relation_name] = relation

	def step_preprocess(self):
		pass

	def update_prices(self):
		self.logic.update_prices()

	def update_volumes(self):
		self.logic.update_volumes()

	def handle_transaction(self, item, volume):
		pass

	def can_pay(self, amount):
		if not self.forbid_negative_cash:
			return True
		return self.cash >= amount

	def max_payment(self, amount):
		if not self.forbid_negative_cash:
			return amount
		return min(self.cash, amount)

	def step_postprocess(self):
		pass

class HouseHold(Agent):
	def __init__(self, name, logic_constructor, initial_cash=0, forbid_negative_cash=False):
		super().__init__(name, logic_constructor, forbid_negative_cash)
		self.relations['labor_consumption'] = None # Need to mount later
		self.cash = initial_cash
		self.step_consumption = 0 # Usually negative
		self.step_labor = 0 # Usually negative
		self.step_money = 0
		self.step_wage_income = 0
		self.step_consumption_spending = 0
		self.step_desired_consumption = 0

	def step_preprocess(self):
		self.step_consumption = 0
		self.step_labor = 0
		self.step_money = 0
		self.step_wage_income = 0
		self.step_consumption_spending = 0
		self.step_desired_consumption = 0

	def handle_transaction(self, item, volume):
		if item == 'consumption':
			self.step_consumption += volume
		elif item == 'labor':
			self.step_labor += volume
		elif item == 'money':
			if self.forbid_negative_cash and self.cash + volume < -1e-12:
				raise ValueError('household cash cannot be negative')
			self.cash += volume
			self.step_money += volume
			if volume > 0:
				self.step_wage_income += volume
			else:
				self.step_consumption_spending += -volume
		else:
			raise Exception('Unknown transaction item for household: ' + item)

class Firm(Agent):
	def __init__(self, name, logic_constructor, initial_cash=0, forbid_negative_cash=False):
		super().__init__(name, logic_constructor, forbid_negative_cash)
		self.relations['labor_consumption'] = None # Need to mount later
		self.cash = initial_cash
		self.step_production = 0
		self.step_labor = 0
		self.step_product_sold = 0 # Usually negative
		self.step_dividend = 0 # Usually negative
		self.step_money = 0
		self.step_wage_bill = 0
		self.step_sales_revenue = 0
		self.step_profit = 0
		self.step_real_profit = 0
		self.step_goods_imbalance = 0
		self.step_profit_goods = 0  # deprecated alias for goods imbalance
		self.step_effective_productivity = None
		self.step_labor_demand = 0

	def step_preprocess(self):
		self.step_production = 0
		self.step_labor = 0
		self.step_product_sold = 0 # Usually negative
		self.step_dividend = 0 # Usually negative
		self.step_money = 0
		self.step_wage_bill = 0
		self.step_sales_revenue = 0
		self.step_profit = 0
		self.step_real_profit = 0
		self.step_goods_imbalance = 0
		self.step_profit_goods = 0  # deprecated alias for goods imbalance
		self.step_effective_productivity = None
		self.step_labor_demand = 0

	def handle_transaction(self, item, volume):
		if item == 'consumption':
			self.step_product_sold += volume
		elif item == 'labor':
			self.step_labor += volume
		elif item == 'money':
			if self.forbid_negative_cash and self.cash + volume < -1e-12:
				raise ValueError('firm cash cannot be negative')
			self.cash += volume
			self.step_money += volume
			if volume > 0:
				self.step_sales_revenue += volume
			else:
				self.step_wage_bill += -volume
			self.step_profit = self.step_sales_revenue - self.step_wage_bill
		else:
			raise Exception('Unknown transaction item for firm: ' + item)

	def step_postprocess(self):
		productivity = getattr(self.logic, 'effective_productivity', self.logic.productivity)
		self.step_effective_productivity = productivity
		self.step_production = self.step_labor * productivity
		self.step_dividend = - self.step_production - self.step_product_sold
		self.step_profit = self.step_sales_revenue - self.step_wage_bill
