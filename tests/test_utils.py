import unittest

import macroABM


class GoodsEquivalentTests(unittest.TestCase):
	def test_goods_equivalent_converts_nominal_money_to_goods(self):
		self.assertEqual(macroABM.goods_equivalent(12, 3), 4)

	def test_goods_equivalent_rejects_zero_goods_price(self):
		with self.assertRaises(ZeroDivisionError):
			macroABM.goods_equivalent(12, 0)

	def test_goods_equivalent_series_converts_pairwise(self):
		self.assertEqual(
			macroABM.goods_equivalent_series([10, 12, 21], [2, 3, 7]),
			[5, 4, 3],
		)

	def test_goods_equivalent_series_requires_matching_lengths(self):
		with self.assertRaises(ValueError):
			macroABM.goods_equivalent_series([10, 12], [2])


if __name__ == '__main__':
	unittest.main()
