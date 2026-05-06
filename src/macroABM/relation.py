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

class MoneyMarket:
	def __init__(self, item, seller, buyer, price, volume=0):
		self.item = item
		self.seller = seller
		self.buyer = buyer
		self.price = price
		self.previous_price = price
		self.volume = volume
		self.supply_volume = volume
		self.demand_volume = volume

	def match_short_side(self):
		self.volume = min(max(0, self.supply_volume), max(0, self.demand_volume))
		return self.volume

	def handle_transactions(self):
		payment = self.price * self.volume
		if payment > 0:
			affordable_payment = self.buyer.max_payment(payment)
			if affordable_payment < payment:
				self.volume = affordable_payment / self.price
				payment = affordable_payment
		self.seller.handle_transaction(self.item, -self.volume)
		self.seller.handle_transaction('money', payment)
		self.buyer.handle_transaction(self.item, self.volume)
		self.buyer.handle_transaction('money', -payment)

	def commit_price(self):
		self.previous_price = self.price
