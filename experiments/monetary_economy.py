import datetime
import os

import matplotlib.pyplot as plt
import pandas as pd
import macroABM


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
num_steps = 100
list_steps = []
list_wages = []
list_goods_prices = []
list_real_wages = []
list_labor_supply = []
list_labor_demand = []
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
list_firm_profit_goods = []

for step in range(num_steps):
	for agt in agents:
		agt.step_preprocess()

	for agt in agents:
		agt.update_prices()

	for agt in agents:
		agt.update_volumes()

	labor_market.match_short_side()
	labor_market.handle_transactions()

	firm.step_postprocess()
	goods_market.supply_volume = firm.step_production
	goods_market.volume = firm.step_production
	goods_market.handle_transactions()

	for market in price_markets:
		market.commit_price()

	list_steps.append(step)
	list_wages.append(labor_market.price)
	list_goods_prices.append(goods_market.price)
	list_real_wages.append(labor_market.price / goods_market.price)
	list_labor_supply.append(labor_market.supply_volume)
	list_labor_demand.append(labor_market.demand_volume)
	list_labor.append(labor_market.volume)
	list_desired_consumption.append(goods_market.demand_volume)
	list_consumption.append(goods_market.volume)
	list_productivity.append(firm.step_effective_productivity)
	list_production.append(firm.step_production)
	list_household_cash.append(household.cash)
	list_firm_cash.append(firm.cash)
	list_household_real_cash.append(household.cash / goods_market.previous_price)
	list_firm_real_cash.append(firm.cash / goods_market.previous_price)
	list_firm_profit.append(firm.step_profit)
	list_firm_profit_goods.append(
		macroABM.goods_equivalent(firm.step_profit, goods_market.previous_price)
	)


# Save results
figures_dir = os.path.join('outputs', 'figures')
data_dir = os.path.join('outputs', 'data')
os.makedirs(figures_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

simulation_df = pd.DataFrame({
	'Step': list_steps,
	'Wage': list_wages,
	'Goods_Price': list_goods_prices,
	'Real_Wage': list_real_wages,
	'Labor_Supply': list_labor_supply,
	'Labor_Demand': list_labor_demand,
	'Labor': list_labor,
	'Desired_Consumption': list_desired_consumption,
	'Consumption': list_consumption,
	'Effective_Productivity': list_productivity,
	'Production': list_production,
	'Household_Cash': list_household_cash,
	'Firm_Cash': list_firm_cash,
	'Household_Real_Cash': list_household_real_cash,
	'Firm_Real_Cash': list_firm_real_cash,
	'Firm_Profit': list_firm_profit,
	'Firm_Profit_Goods': list_firm_profit_goods,
})

timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
csv_file = os.path.join(data_dir, f'monetary_economy_{timestamp}.csv')
simulation_df.to_csv(csv_file, index=False)
print(f'Simulation data saved to {csv_file}')


# Plot results
figure, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

axes[0].plot(list_steps, list_wages, label='Wage')
axes[0].plot(list_steps, list_goods_prices, label='Goods Price')
axes[0].plot(list_steps, list_firm_profit, label='Firm Profit')
axes[0].set_ylabel('Nominal Value')
axes[0].set_title('Monetary Economy Simulation')
axes[0].legend()
axes[0].grid(True)

axes[1].plot(list_steps, list_real_wages, label='Wage in Goods')
axes[1].plot(list_steps, list_labor, label='Matched Labor')
axes[1].plot(list_steps, list_desired_consumption, label='Desired Consumption')
axes[1].plot(list_steps, list_consumption, label='Realized Consumption')
axes[1].plot(list_steps, list_productivity, label='Effective Productivity')
axes[1].plot(list_steps, list_firm_profit_goods, label='Firm Profit in Goods')
axes[1].set_ylabel('Equivalent Goods / Real Quantity')
axes[1].legend()
axes[1].grid(True)

axes[2].plot(list_steps, list_household_cash, label='Household Cash')
axes[2].plot(list_steps, list_firm_cash, label='Firm Cash')
axes[2].plot(list_steps, list_household_real_cash, label='Household Cash in Goods')
axes[2].plot(list_steps, list_firm_real_cash, label='Firm Cash in Goods')
axes[2].set_xlabel('Step')
axes[2].set_ylabel('Cash Balances')
axes[2].legend()
axes[2].grid(True)

figure.tight_layout()

output_file = os.path.join(figures_dir, 'monetary_economy.png')
plt.savefig(output_file, dpi=300)
print(f'Figure saved to {output_file}')
