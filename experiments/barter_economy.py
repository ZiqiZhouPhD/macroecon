# Create agents and relations
# In each step
# 	impose external changes
# 	update agent behaviors, for each market
# 		set prices
# 		set volumes
# 	execute relation transactions

import os
import matplotlib.pyplot as plt
import macroABM

# Set up
household = macroABM.HouseHold('Household', macroABM.LinearHouseHoldLogic)
firm = macroABM.Firm('Firm', macroABM.LinearFirmLogic)
labor_consumption_relation = macroABM.BarterMarket(
	items = ('labor', 'consumption'),
	agents = (household, firm),
	volumes = [1, 1]
)
household.mount_relation('labor_consumption', labor_consumption_relation)
firm.mount_relation('labor_consumption', labor_consumption_relation)
agents = [household, firm]
relations = [labor_consumption_relation]

# Simulation loop
num_steps = 100
list_steps = []
list_labor_prices = []
list_labors = []
list_consumptions = []
list_productions = []
list_dividends = []
for step in range(num_steps):
	# Preprocess
	for agt in agents:
		agt.step_preprocess()
	
	# Update prices
	for agt in agents:
		agt.update_prices()
	# labor_consumption_relation.price = step * 0.1 + 1 # Sweep price for testing
	
	# Update volumes
	for agt in agents:
		agt.update_volumes()
	
	# Handle transactions
	for rel in relations:
		rel.handle_transactions()
	
	# Postprocess
	for agt in agents:
		agt.step_postprocess()
	
	# Record step results
	list_steps.append(step)
	list_labor_prices.append(labor_consumption_relation.price)
	list_labors.append(labor_consumption_relation.volumes[0])
	list_consumptions.append(labor_consumption_relation.volumes[1])
	list_productions.append(firm.step_production)
	list_dividends.append(-firm.step_dividend)

# Ensure output directories exist
figures_dir = os.path.join('outputs', 'figures')
os.makedirs(figures_dir, exist_ok=True)

import pandas as pd

# Ensure output directory exists
data_dir = os.path.join('outputs', 'data')
os.makedirs(data_dir, exist_ok=True)

# Combine all simulation results into a DataFrame
simulation_df = pd.DataFrame({
	"Step": list_steps,
	"Labor_Price": list_labor_prices,
	"Labor_Supply": list_labors,
	"Consumption": list_consumptions,
	"Production": list_productions,
	"Dividends": list_dividends
})

# Save to CSV with timestamp for versioning
import datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = os.path.join(data_dir, f"barter_economy_{timestamp}.csv")

simulation_df.to_csv(csv_file, index=False)
print(f"Simulation data saved to {csv_file}")

# Plot results
plt.figure(figsize=(12, 8))

plt.plot(list_steps, list_labor_prices, label="Labor Prices")
plt.plot(list_steps, list_labors, label="Labor Supply")
plt.plot(list_steps, list_consumptions, label="Consumption Demand")
plt.plot(list_steps, list_productions, label="Production Output")
plt.plot(list_steps, list_dividends, label="Firm Dividends")

plt.xlabel("Step")
plt.ylabel("Value")
plt.title("Barter Economy Simulation")
plt.legend()
plt.grid(True)
plt.tight_layout()

# Save figure to outputs folder
output_file = os.path.join(figures_dir, "barter_economy.png")
plt.savefig(output_file, dpi=300)
print(f"Figure saved to {output_file}")

# Optionally display
plt.show()