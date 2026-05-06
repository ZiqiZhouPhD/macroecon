def goods_equivalent(nominal_value, goods_price):
	if goods_price == 0:
		raise ZeroDivisionError('goods price cannot be zero')
	return nominal_value / goods_price


def goods_equivalent_series(nominal_values, goods_prices):
	if len(nominal_values) != len(goods_prices):
		raise ValueError('nominal values and goods prices must have the same length')
	return [
		goods_equivalent(nominal_value, goods_price)
		for nominal_value, goods_price in zip(nominal_values, goods_prices)
	]
