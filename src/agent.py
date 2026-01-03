class Agent:
	def __init__(self, name, logic_constructor):
		self.name = name
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

	def step_postprocess(self):
		pass

class HouseHold(Agent):
	def __init__(self, name, logic_constructor):
		super().__init__(name, logic_constructor)
		self.relations['labor_consumption'] = None # Need to mount later
		self.step_consumption = 0 # Usually negative
		self.step_labor = 0 # Usually negative
	
	def step_preprocess(self):
		self.step_consumption = 0
		self.step_labor = 0
	
	def handle_transaction(self, item, volume):
		if item == 'consumption':
			self.step_consumption += volume
		elif item == 'labor':
			self.step_labor += volume
		else:
			raise Exception('Unknown transaction item for household: ' + item)

class Firm(Agent):
	def __init__(self, name, logic_constructor):
		super().__init__(name, logic_constructor)
		self.relations['labor_consumption'] = None # Need to mount later
		self.step_production = 0
		self.step_labor = 0
		self.step_product_sold = 0 # Usually negative
		self.step_dividend = 0 # Usually negative
	
	def step_preprocess(self):
		self.step_production = 0
		self.step_labor = 0
		self.step_product_sold = 0 # Usually negative
		self.step_dividend = 0 # Usually negative
	
	def handle_transaction(self, item, volume):
		if item == 'consumption':
			self.step_product_sold += volume
		elif item == 'labor':
			self.step_labor += volume
		else:
			raise Exception('Unknown transaction item for firm: ' + item)
	
	def step_postprocess(self):
		self.step_production = self.step_labor * self.logic.productivity
		self.step_dividend = - self.step_production - self.step_product_sold