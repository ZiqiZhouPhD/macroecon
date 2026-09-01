import math

from scipy.optimize import least_squares, minimize

from . import functions
from .optimizer import StepwiseNelderMead2D

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

class MonetaryHouseHoldLogic(HouseHoldLogic):
	def __init__(self, household):
		self.household = household
		self.elasticity = 0.2
		self.labor_0 = 1
		self.real_wage_0 = None
		self.target_real_cash = 2
		self.propensity_income = 0.8
		self.propensity_wealth = 0.15

	def update_volumes(self):
		labor_market = self.household.relations['labor']
		goods_market = self.household.relations['goods']
		real_wage = labor_market.price / goods_market.price
		if self.real_wage_0 is None:
			self.real_wage_0 = real_wage

		labor_supply = self.labor_0 * (real_wage / self.real_wage_0) ** self.elasticity
		# Cash is a beginning-of-step stock, but its purchasing power is set by
		# the price that applies to this step's decisions.  Using the previous
		# price here makes a candidate nominal price invisible to current demand
		# and introduces an artificial one-step lag.
		real_cash = self.household.cash / goods_market.price
		real_income = labor_market.price * labor_supply / goods_market.price
		buffer_gap = real_cash - self.target_real_cash
		desired_consumption = (
			self.propensity_income * real_income
			+ self.propensity_wealth * buffer_gap
		)
		desired_consumption = max(0, desired_consumption)

		labor_market.supply_volume = labor_supply
		goods_market.demand_volume = desired_consumption
		self.household.step_desired_consumption = desired_consumption

class MonetaryFirmLogic(FirmLogic):
	def __init__(self, firm):
		self.firm = firm
		self.productivity = 2
		self.effective_productivity = self.productivity
		self.liquidity_scale = 4
		self.min_productivity_factor = 0.5
		self.max_productivity_factor = 1.25

		# The economic model treats prices as an instantaneous optimum at the
		# current state.  The former one-evaluation-per-economic-step behavior is
		# retained as an explicit compatibility mode, but is not the default.
		self.price_optimization_mode = 'instantaneous'
		self._nm = None             # legacy StepwiseNelderMead2D tracker
		self._nm_result = None      # latest frozen-state scipy OptimizeResult
		self._nm_last_profit = None
		self.nm_initial_log_size = 1e-3  # approximately 0.1% initial probes
		# Retained for the legacy stepwise Nelder-Mead compatibility path.
		self.nm_warm_start_log_size = 3e-3
		self.nm_solve_log_tolerance = 3e-5
		self.nm_solve_profit_tolerance = 1e-8
		self.nm_solve_max_iterations = 200
		self.price_solve_tolerance = 1e-12
		self.nm_solve_count = 0
		self.nm_last_iterations = 0
		self.nm_last_evaluations = 0
		self.nm_last_converged = False
		self.nm_last_predicted_profit = None
		self.price_solver_last_method = None
		self.nominal_price_upper_bound = None
		# A 0.003% log-price radius keeps exploration persistent without making
		# the optimizer's probes dominate the dt=0.001 economic dynamics.
		self.nm_min_log_size = 3e-5
		self.nm_max_vertex_age = 20  # measured in objective evaluations
		self.nm_max_log_step = 1e-3  # at most about 0.1% per tracking proposal

	def get_liquidity_factor(self, real_cash):
		real_cash = max(0, real_cash)
		raw = (
			self.min_productivity_factor
			+ (self.max_productivity_factor - self.min_productivity_factor)
			* real_cash / (real_cash + self.liquidity_scale)
		)
		return min(self.max_productivity_factor, max(self.min_productivity_factor, raw))

	def record_profit(self, profit_rate):
		self._nm_last_profit = profit_rate

	def _initialize_household_real_wage_reference(self):
		labor_market = self.firm.relations['labor']
		goods_market = self.firm.relations['goods']
		household_logic = goods_market.buyer.logic
		if household_logic.real_wage_0 is None:
			household_logic.real_wage_0 = labor_market.price / goods_market.price

	def _evaluate_candidate(self, wage, goods_price):
		"""Evaluate the firm's expected plan and possible realized settlement."""
		if wage <= 0 or goods_price <= 0:
			return None

		goods_market = self.firm.relations['goods']
		household = goods_market.buyer
		household_logic = household.logic
		real_wage = wage / goods_price
		labor_supply = household_logic.labor_0 * (
			real_wage / household_logic.real_wage_0
		) ** household_logic.elasticity
		household_real_cash = household.cash / goods_price
		desired_consumption = max(
			0,
			household_logic.propensity_income * real_wage * labor_supply
			+ household_logic.propensity_wealth
			* (household_real_cash - household_logic.target_real_cash),
		)
		firm_real_cash = self.firm.cash / goods_price
		effective_productivity = (
			self.productivity * self.get_liquidity_factor(firm_real_cash)
		)
		production = labor_supply * effective_productivity
		realized_consumption = min(desired_consumption, production)
		# The firm chooses prices under expected goods-market clearing, so its
		# payoff is output less the wage bill valued in goods.  The ex-post gap
		# production - realized_consumption is a market imbalance, not profit.
		expected_real_profit = production - real_wage * labor_supply
		nominal_operating_profit = (
			goods_price * realized_consumption - wage * labor_supply
		)
		return (
			labor_supply,
			desired_consumption,
			production,
			realized_consumption,
			expected_real_profit,
			nominal_operating_profit,
		)

	def evaluate_real_profit(self, wage, goods_price):
		"""Expected operating profit in goods, assuming production is sold."""
		outcome = self._evaluate_candidate(wage, goods_price)
		return -math.inf if outcome is None else outcome[4]

	def evaluate_operating_profit(self, wage, goods_price):
		"""Nominal sales less wage payments; not the pricing objective."""
		outcome = self._evaluate_candidate(wage, goods_price)
		return -math.inf if outcome is None else outcome[5]

	def _market_clearing_gap(self, log_prices):
		wage, goods_price = (math.exp(value) for value in log_prices)
		outcome = self._evaluate_candidate(wage, goods_price)
		return outcome[1] - outcome[2]

	def _expected_clearing_first_order_conditions(self, log_prices):
		"""Clearing plus the constrained expected-real-profit condition."""
		wage, goods_price = (math.exp(value) for value in log_prices)
		real_wage = wage / goods_price
		goods_market = self.firm.relations['goods']
		household = goods_market.buyer
		household_logic = household.logic
		elasticity = household_logic.elasticity
		labor = household_logic.labor_0 * (
			real_wage / household_logic.real_wage_0
		) ** elasticity
		labor_real_wage_derivative = elasticity * labor / real_wage

		firm_cash = self.firm.cash
		liquidity_denominator = firm_cash + self.liquidity_scale * goods_price
		productivity_spread = (
			self.max_productivity_factor - self.min_productivity_factor
		)
		productivity = self.productivity * (
			self.min_productivity_factor
			+ productivity_spread * firm_cash / liquidity_denominator
		)
		productivity_price_derivative = (
			-self.productivity
			* productivity_spread
			* firm_cash
			* self.liquidity_scale
			/ liquidity_denominator ** 2
		)

		income_propensity = household_logic.propensity_income
		wealth_propensity = household_logic.propensity_wealth
		desired_consumption = (
			income_propensity * real_wage * labor
			+ wealth_propensity
			* (household.cash / goods_price - household_logic.target_real_cash)
		)
		production = productivity * labor
		market_gap = desired_consumption - production

		gap_real_wage_derivative = (
			income_propensity
			* (labor + real_wage * labor_real_wage_derivative)
			- productivity * labor_real_wage_derivative
		)
		gap_price_derivative = (
			-wealth_propensity * household.cash / goods_price ** 2
			- productivity_price_derivative * labor
		)
		profit_real_wage_derivative = (
			labor_real_wage_derivative * (productivity - real_wage)
			- labor
		)
		profit_price_derivative = productivity_price_derivative * labor
		# Use log-coordinate derivatives for comparable residual scales.
		constrained_foc = (
			real_wage
			* profit_real_wage_derivative
			* goods_price
			* gap_price_derivative
			- goods_price
			* profit_price_derivative
			* real_wage
			* gap_real_wage_derivative
		)
		return market_gap, constrained_foc

	def _find_expected_clearing_stationary(self, start_log_prices):
		lower_log_price = math.log(1e-3)
		upper_log_price = math.log(self.nominal_price_upper_bound)
		start = [
			min(upper_log_price, max(lower_log_price, value))
			for value in start_log_prices
		]
		result = least_squares(
			self._expected_clearing_first_order_conditions,
			start,
			bounds=(
				[lower_log_price, lower_log_price],
				[upper_log_price, upper_log_price],
			),
			xtol=self.price_solve_tolerance,
			ftol=self.price_solve_tolerance,
			gtol=self.price_solve_tolerance,
			max_nfev=50,
		)
		wage, goods_price = (math.exp(value) for value in result.x)
		outcome = self._evaluate_candidate(wage, goods_price)
		residual = max(
			abs(value)
			for value in self._expected_clearing_first_order_conditions(result.x)
		)
		result.objective_value = outcome[4]
		result.is_valid = (
			result.success
			and residual <= 1e-7
			and outcome[1] > 0
			and max(wage, goods_price)
			< self.nominal_price_upper_bound * (1 - 1e-8)
		)
		return result

	def _economic_start(self):
		"""Construct a scale-aware starting point near the clearing branch."""
		labor_market = self.firm.relations['labor']
		goods_market = self.firm.relations['goods']
		household = goods_market.buyer
		household_logic = household.logic
		current_price = goods_market.price
		firm_real_cash = self.firm.cash / current_price
		productivity = self.productivity * self.get_liquidity_factor(
			firm_real_cash
		)
		elasticity = household_logic.elasticity
		real_wage = elasticity * productivity / (elasticity + 1)
		labor = household_logic.labor_0 * (
			real_wage / household_logic.real_wage_0
		) ** elasticity
		real_balance_denominator = (
			household_logic.target_real_cash
			+ (
				productivity
				- household_logic.propensity_income * real_wage
			)
			* labor / household_logic.propensity_wealth
		)
		goods_price = household.cash / real_balance_denominator
		goods_price = min(
			self.nominal_price_upper_bound,
			max(1e-3, goods_price),
		)
		wage = min(
			self.nominal_price_upper_bound,
			max(1e-3, real_wage * goods_price),
		)
		return [math.log(wage), math.log(goods_price)]

	def _solve_instantaneous_prices(self):
		"""Maximize expected real profit subject to expected market clearing."""
		labor_market = self.firm.relations['labor']
		goods_market = self.firm.relations['goods']
		w0, p0 = labor_market.price, goods_market.price
		lower_log_price = math.log(1e-3)
		total_cash = self.firm.cash + goods_market.buyer.cash
		if self.nominal_price_upper_bound is None:
			self.nominal_price_upper_bound = max(
				1e3,
				100 * w0,
				100 * p0,
				100 * total_cash,
			)
		upper_price = self.nominal_price_upper_bound
		upper_log_price = math.log(upper_price)
		z0 = [math.log(w0), math.log(p0)]
		result = None
		method = None
		total_evaluations = 0
		if self.nm_solve_count:
			stationary_result = self._find_expected_clearing_stationary(z0)
			total_evaluations += stationary_result.nfev
			if stationary_result.is_valid:
				result = stationary_result
				method = 'expected_clearing_foc'

		def negative_expected_real_profit(log_prices):
			wage, goods_price = (math.exp(value) for value in log_prices)
			return -self.evaluate_real_profit(wage, goods_price)

		bounds = [
			(lower_log_price, upper_log_price),
			(lower_log_price, upper_log_price),
		]
		if result is None:
			starts = [z0, self._economic_start()]
			results = []
			for start in starts:
				if results and max(
					abs(left - right) for left, right in zip(start, starts[0])
				) < 1e-10:
					continue
				candidate = minimize(
				negative_expected_real_profit,
				start,
				method='SLSQP',
				bounds=bounds,
				constraints={
					'type': 'eq',
					'fun': self._market_clearing_gap,
				},
				options={
					'ftol': self.price_solve_tolerance,
					'maxiter': self.nm_solve_max_iterations,
				},
			)
				total_evaluations += candidate.nfev
				wage, goods_price = (
					math.exp(value) for value in candidate.x
				)
				outcome = self._evaluate_candidate(wage, goods_price)
				clearing_tolerance = 1e-7 * max(1, outcome[2])
				candidate.is_valid = (
					candidate.success
					and outcome[1] > 0
					and abs(outcome[1] - outcome[2]) <= clearing_tolerance
					and max(wage, goods_price) < upper_price * (1 - 1e-8)
				)
				if candidate.is_valid:
					results.append(candidate)

			if not results:
				raise RuntimeError(
					'expected-clearing price optimization failed at solve '
					f'{self.nm_solve_count} with household_cash='
					f'{goods_market.buyer.cash:.12g}, firm_cash='
					f'{self.firm.cash:.12g}, wage={w0:.12g}, '
					f'goods_price={p0:.12g}'
				)
			result = min(results, key=lambda candidate: candidate.fun)
			method = 'expected_clearing_slsqp'
		wage, goods_price = (math.exp(value) for value in result.x)

		self._nm_result = result
		self.nm_solve_count += 1
		self.nm_last_iterations = getattr(result, 'nit', 0)
		self.nm_last_evaluations = total_evaluations
		self.nm_last_converged = result.success
		self.price_solver_last_method = method
		self.nm_last_predicted_profit = self.evaluate_real_profit(
			wage,
			goods_price,
		)
		return wage, goods_price

	def _advance_stepwise_prices(self):
		"""Compatibility path for the former one-evaluation-per-step solver."""
		labor_market = self.firm.relations['labor']
		goods_market = self.firm.relations['goods']
		if self._nm is None:
			w0, p0 = labor_market.price, goods_market.price
			seed_scale = math.exp(self.nm_initial_log_size)
			self._nm = StepwiseNelderMead2D(
				seeds=[
					(w0, p0),
					(w0 * seed_scale, p0),
					(w0, p0 * seed_scale),
				],
				lower_bounds=(1e-3, 1e-3),
				min_simplex_size=self.nm_min_log_size,
				max_vertex_age=self.nm_max_vertex_age,
				use_log_coordinates=True,
				max_proposal_step=self.nm_max_log_step,
			)
		return self._nm.advance(self._nm_last_profit)

	def update_prices(self):
		labor_market = self.firm.relations['labor']
		goods_market = self.firm.relations['goods']
		self._initialize_household_real_wage_reference()
		if self.price_optimization_mode == 'instantaneous':
			w, p = self._solve_instantaneous_prices()
		elif self.price_optimization_mode == 'stepwise':
			w, p = self._advance_stepwise_prices()
		else:
			raise ValueError(
				'price_optimization_mode must be instantaneous or stepwise'
			)
		labor_market.price = w
		goods_market.price = p

		# Value the beginning-of-step cash stock at the candidate current price.
		# This makes nominal price level economically visible in the same
		# objective evaluation instead of only affecting the following step.
		current_real_cash = self.firm.cash / goods_market.price
		self.effective_productivity = (
			self.productivity * self.get_liquidity_factor(current_real_cash)
		)
		self.firm.step_effective_productivity = self.effective_productivity

	def update_volumes(self):
		pass
