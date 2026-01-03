class LinearFunction:
	def __init__(self, intercept, slope):
		self.intercept = intercept
		self.slope = slope
	
	def evaluate(self, x):
		return self.intercept + self.slope * x

class QuadraticFunction:
	def __init__(self, a, b, c):
		self.a = a
		self.b = b
		self.c = c

class LaurentFunction:
	def __init__(self, A, B):
		self.A = A # List of coeffs for [1, X, X^2, ...]
		self.B = B # List of coeffs for [..., X^-2, X^-1]