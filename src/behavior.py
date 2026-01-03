class Behavior: pass

class QuantityPriceBehavior(Behavior):
	def get_quantity_for_price(self, price):
		raise NotImplementedError("This method should be implemented by subclasses.")

class TaylorQuantityPriceBehavior(QuantityPriceBehavior):
	def __init__(self, point0, slope, quadratic=0, range=None):
		self.price0, self.quantity0 = point0
		self.slope = slope
		self.quadratic = quadratic
		if range is None:
			self.price_low = self.price0 * 0.8
			self.price_high = self.price0 * 1.2
		else:
			self.price_low, self.price_high = range

	def get_quantity_for_price(self, price):
		if not (self.price_low <= price <= self.price_high):
			raise ValueError(f"Price {price} is out of range.")
		return self.quantity0 + self.slope * (price - self.price0) + self.quadratic * (price - self.price0) ** 2