class Relation:
	def __init__(self):
		# Dicts are labeled by agent names
		self.agents = dict()

	def handle_transactions(self):
		pass

class Market:
	def __init__(self):
		self.agents_buy = []
		self.price = None
		self.volume = None

class BarterMarket:
	def __init__(self, items, agents, volumes):
		self.items = items # (None, None) # Item names
		self.agents = agents # (None, None)
		self.volumes = volumes # (None, None)
		self.price = volumes[0] / volumes[1] # None # Price of second item in first item

	def handle_transactions(self):
		for i in range(2):
			self.agents[i].handle_transaction(self.items[i], -self.volumes[i])
			self.agents[i].handle_transaction(self.items[1-i], self.volumes[1-i])
