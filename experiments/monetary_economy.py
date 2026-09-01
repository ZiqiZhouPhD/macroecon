import datetime
import math
import os

import matplotlib.pyplot as plt
import pandas as pd
import macroABM


# Parameters
dt = 0.001            # fraction of an economic period per simulation step
dividend_rate = 0.1

# Set up
household = macroABM.HouseHold(
	'Household',
	macroABM.MonetaryHouseHoldLogic,
	initial_cash=5,
	forbid_negative_cash=True
)
firm = macroABM.Firm(
	'Firm',
	macroABM.MonetaryFirmLogic,
	initial_cash=5,
	forbid_negative_cash=True
)

labor_market = macroABM.MoneyMarket(
	item='labor',
	seller=household,
	buyer=firm,
	price=1,
	volume=1
)
goods_market = macroABM.MoneyMarket(
	item='consumption',
	seller=firm,
	buyer=household,
	price=1,
	volume=1
)

household.mount_relation('labor', labor_market)
household.mount_relation('goods', goods_market)
firm.mount_relation('labor', labor_market)
firm.mount_relation('goods', goods_market)

agents = [household, firm]
price_markets = [labor_market, goods_market]


# Simulation loop
total_time = 50.0
num_steps = round(total_time / dt)
list_time = []
list_wages = []
list_goods_prices = []
list_real_wages = []
list_labor_supply = []
list_labor = []
list_desired_consumption = []
list_consumption = []
list_productivity = []
list_production = []
list_household_cash = []
list_firm_cash = []
list_household_real_cash = []
list_firm_real_cash = []
list_firm_profit = []
list_firm_profit_real = []
list_firm_profit_goods = []
list_dividends = []
list_nm_restart_count = []
list_nm_restart_event = []
list_nm_restart_reason = []
list_nm_simplex_size = []
list_nm_oldest_vertex_age = []
list_nm_iterations = []
list_nm_evaluations = []
list_nm_converged = []
list_price_solver_method = []
list_nm_predicted_profit = []
list_nm_objective_error = []
previous_nm_restart_count = 0

for step in range(num_steps):
	# 1. Reset step accumulators.
	for agt in agents:
		agt.step_preprocess()

	# 2. Firm solves the frozen-state (wage, goods price) problem and computes
	#    productivity from beginning-of-step cash at the candidate current price.
	for agt in agents:
		agt.update_prices()
	nm = firm.logic._nm
	if nm is None:
		nm_restart_event = 0
		nm_restart_reason = ''
		nm_simplex_size = None
		nm_oldest_vertex_age = None
	else:
		nm_restart_event = nm.restart_count - previous_nm_restart_count
		nm_restart_reason = nm.last_restart_reason if nm_restart_event else ''
		previous_nm_restart_count = nm.restart_count
		nm_simplex_size = nm.simplex_size
		nm_oldest_vertex_age = nm.oldest_vertex_age

	# 3. Household chooses labor supply and desired consumption.
	for agt in agents:
		agt.update_volumes()

	# 4. Labor market: firm absorbs all household supply — no short-side rationing.
	#    Volume is rate * dt so cash flows integrate correctly over time.
	labor_market.volume = labor_market.supply_volume * dt
	labor_market.handle_transactions()

	# 5. Production (step_labor already equals rate * dt from the market settlement).
	firm.step_production = firm.step_labor * firm.step_effective_productivity

	# 6. Goods market: demand-determined — household buys desired consumption up to supply.
	goods_market.volume = min(goods_market.demand_volume * dt, firm.step_production)
	goods_market.handle_transactions()

	# 7. Any production-sales gap is an ex-post market imbalance, not profit.
	goods_imbalance = firm.step_production - goods_market.volume
	firm.step_goods_imbalance = goods_imbalance
	firm.step_profit_goods = goods_imbalance  # compatibility field

	# 8. Real operating profit values the wage bill in goods.  The firm chose
	#    prices under expected clearing before this actual settlement occurred.
	real_profit = (
		firm.step_production
		- labor_market.price / goods_market.price * firm.step_labor
	)
	firm.step_real_profit = real_profit
	firm.logic.record_profit(real_profit / dt)

	# 9. Dividend transfer proportional to log(firm_cash / household_cash), modelling
	#    the symmetric pressure of household investment and firm profit distribution.
	step_dividend = 0.0
	if firm.cash > 1e-9 and household.cash > 1e-9:
		log_ratio = math.log(firm.cash / household.cash)
		step_dividend = dividend_rate * dt * log_ratio
		# Cap so neither side goes below zero.
		step_dividend = min(step_dividend, firm.cash)
		step_dividend = max(step_dividend, -household.cash)
		firm.cash -= step_dividend
		household.cash += step_dividend

	# 10. Commit prices for price-history bookkeeping.
	for market in price_markets:
		market.commit_price()

	list_time.append(step * dt)
	list_wages.append(labor_market.price)
	list_goods_prices.append(goods_market.price)
	list_real_wages.append(labor_market.price / goods_market.price)
	list_labor_supply.append(labor_market.supply_volume)
	list_labor.append(firm.step_labor / dt)
	list_desired_consumption.append(goods_market.demand_volume)
	list_consumption.append(goods_market.volume / dt)
	list_productivity.append(firm.step_effective_productivity)
	list_production.append(firm.step_production / dt)
	list_household_cash.append(household.cash)
	list_firm_cash.append(firm.cash)
	list_household_real_cash.append(household.cash / goods_market.previous_price)
	list_firm_real_cash.append(firm.cash / goods_market.previous_price)
	list_firm_profit.append(firm.step_profit / dt)
	list_firm_profit_real.append(real_profit / dt)
	list_firm_profit_goods.append(goods_imbalance / dt)
	list_dividends.append(step_dividend / dt)
	list_nm_restart_count.append(previous_nm_restart_count)
	list_nm_restart_event.append(nm_restart_event)
	list_nm_restart_reason.append(nm_restart_reason)
	list_nm_simplex_size.append(nm_simplex_size)
	list_nm_oldest_vertex_age.append(nm_oldest_vertex_age)
	list_nm_iterations.append(firm.logic.nm_last_iterations)
	list_nm_evaluations.append(firm.logic.nm_last_evaluations)
	list_nm_converged.append(firm.logic.nm_last_converged)
	list_price_solver_method.append(firm.logic.price_solver_last_method)
	list_nm_predicted_profit.append(firm.logic.nm_last_predicted_profit)
	list_nm_objective_error.append(
		None
		if firm.logic.nm_last_predicted_profit is None
		else real_profit / dt - firm.logic.nm_last_predicted_profit
	)


# Save results
figures_dir = os.path.join('outputs', 'figures')
data_dir = os.path.join('outputs', 'data')
os.makedirs(figures_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

simulation_df = pd.DataFrame({
	'Time': list_time,
	'Wage': list_wages,
	'Goods_Price': list_goods_prices,
	'Real_Wage': list_real_wages,
	'Labor_Supply': list_labor_supply,
	'Labor': list_labor,
	'Desired_Consumption': list_desired_consumption,
	'Consumption': list_consumption,
	'Effective_Productivity': list_productivity,
	'Production': list_production,
	'Household_Cash': list_household_cash,
	'Firm_Cash': list_firm_cash,
	'Household_Real_Cash': list_household_real_cash,
	'Firm_Real_Cash': list_firm_real_cash,
	'Firm_Profit_Nominal': list_firm_profit,
	'Firm_Profit_Real': list_firm_profit_real,
	'Goods_Imbalance': list_firm_profit_goods,
	# Retained legacy name; this column is an imbalance, not economic profit.
	'Firm_Profit_Goods': list_firm_profit_goods,
	'Dividend': list_dividends,
	'NM_Restart_Count': list_nm_restart_count,
	'NM_Restart_Event': list_nm_restart_event,
	'NM_Restart_Reason': list_nm_restart_reason,
	'NM_Simplex_Size': list_nm_simplex_size,
	'NM_Oldest_Vertex_Age': list_nm_oldest_vertex_age,
	'NM_Iterations': list_nm_iterations,
	'NM_Evaluations': list_nm_evaluations,
	'NM_Converged': list_nm_converged,
	'Price_Solver_Method': list_price_solver_method,
	'Price_Solver_Predicted_Real_Profit': list_nm_predicted_profit,
	'Price_Solver_Objective_Error': list_nm_objective_error,
	# Retained aliases for compatibility with earlier result readers.
	'NM_Predicted_Profit': list_nm_predicted_profit,
	'NM_Objective_Error': list_nm_objective_error,
})

timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
csv_file = os.path.join(data_dir, f'monetary_economy_{timestamp}.csv')
simulation_df.to_csv(csv_file, index=False)
print(f'Simulation data saved to {csv_file}')
print(
	f'Price optimization mode: {firm.logic.price_optimization_mode}; '
	f'solves={firm.logic.nm_solve_count}, '
	f'last method={firm.logic.price_solver_last_method}, '
	f'last evaluations={firm.logic.nm_last_evaluations}, '
	f'solver tolerance={firm.logic.price_solve_tolerance:g}'
)


# Plot results
figure, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

axes[0].plot(list_time, list_wages, label='Wage')
axes[0].plot(list_time, list_goods_prices, label='Goods Price')
axes[0].plot(list_time, list_firm_profit, label='Firm Profit (nominal)')
axes[0].set_ylabel('Nominal Value')
axes[0].set_title('Monetary Economy Simulation')
axes[0].legend()
axes[0].grid(True)

axes[1].plot(list_time, list_real_wages, label='Wage in Goods')
axes[1].plot(list_time, list_labor, label='Matched Labor')
axes[1].plot(list_time, list_desired_consumption, label='Desired Consumption')
axes[1].plot(list_time, list_consumption, label='Realized Consumption')
axes[1].plot(list_time, list_productivity, label='Effective Productivity')
axes[1].plot(list_time, list_firm_profit_real, label='Firm Real Profit')
axes[1].plot(list_time, list_firm_profit_goods, label='Goods Imbalance')
axes[1].set_ylabel('Equivalent Goods / Real Quantity')
axes[1].legend()
axes[1].grid(True)

axes[2].plot(list_time, list_household_cash, label='Household Cash')
axes[2].plot(list_time, list_firm_cash, label='Firm Cash')
axes[2].plot(list_time, list_dividends, label='Dividend (firm→household)')
axes[2].set_xlabel('Time')
axes[2].set_ylabel('Cash / Dividend')
axes[2].legend()
axes[2].grid(True)

figure.tight_layout()

output_file = os.path.join(figures_dir, 'monetary_economy.png')
plt.savefig(output_file, dpi=300)
print(f'Figure saved to {output_file}')
