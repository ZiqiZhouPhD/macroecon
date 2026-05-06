# Macroeconomic Agent-Based Simulation Sandbox

A modular, agent-based macroeconomic simulation framework designed to study
emergent macro dynamics from micro-level behavioral rules.

The project currently contains two working example economies:

- `experiments/barter_economy.py`: the original moneyless baseline, where one household and one firm barter labor for consumption goods.
- `experiments/monetary_economy.py`: a monetary extension, where labor and goods trade through money, agents hold cash, and firm productivity depends on real liquidity.

This is still an early-stage research sandbox. The monetary model is functional, but its behavior rules are still being tuned.

---

## Current Features

- Discrete-time agent-based simulation
- Household and firm agent types
- Backward-compatible barter market
- Monetary market settlement through cash payments
- Optional nonnegative-cash constraint at the agent level
- Behavioral logic separated from agent state
- Real-balance calculations: cash influences decisions only after conversion into goods-equivalent purchasing power
- CSV output and matplotlib visualization
- Standard-library test suite under `tests/`

---

## Code Structure

```text
src/
  macroABM/
    __init__.py    # flat re-exports of public classes and helpers
    agent.py       # Agent, HouseHold, Firm state and cash accounting
    behavior.py    # price-quantity behavioral policies
    relation.py    # BarterMarket and MoneyMarket
    logic.py       # barter and monetary decision logic
    functions.py   # math utility classes
    utils.py       # goods-equivalent conversion helpers

experiments/
  barter_economy.py    # moneyless baseline simulation
  monetary_economy.py  # monetary simulation with cash/liquidity

tests/
  test_barter.py
  test_monetary.py
  test_utils.py

outputs/
  figures/        # generated plots
  data/           # generated CSV files

docs/
  models.md       # comparison of ABM, DGE, DSGE, and hybrid model types

notes/
  todo.md         # planned extensions and future improvements
```

---

## Getting Started

Install the package in editable mode:

```bash
pip install -e .
```

Run the barter baseline:

```bash
python experiments/barter_economy.py
```

Run the monetary experiment:

```bash
python experiments/monetary_economy.py
```

Run tests:

```bash
python -m unittest discover -v
```

Simulation outputs are saved under `outputs/`.

---

## Monetary Model Summary

The monetary extension splits the old labor-consumption barter relation into two money-mediated markets:

```text
labor market:
  household sells labor
  firm buys labor
  price = wage

goods market:
  firm sells consumption goods
  household buys consumption goods
  price = goods price
```

Agents can hold cash:

- `HouseHold.cash`
- `Firm.cash`

Cash is not meant to influence behavior directly as a nominal value. Decision logic converts cash into real purchasing power:

```python
real_cash = cash / previous_goods_price
```

The monetary experiment currently enables:

```python
forbid_negative_cash=True
```

When this option is enabled, `MoneyMarket` caps transaction volume to what the buyer can afford, and direct overdraft transactions raise an error.

---

## Current Monetary Dynamics

The current monetary experiment starts with:

```text
Household cash = 5
Firm cash = 5
Wage = 1
Goods price = 1
Negative cash forbidden
```

The model runs, but it currently tends toward a liquidity-constrained corner: firm profits move cash from the household to the firm, the household eventually reaches the zero-cash floor, and output falls to a very low level. This is useful as a diagnostic result, not yet the desired well-balanced equilibrium example.

Next work should adjust the monetary behavior rules so money circulates more naturally, for example through dividends, wage adjustment, price adjustment, or household/firm rules that produce a more stable interior equilibrium.

---

## Planned Extensions

See [`notes/todo.md`](notes/todo.md) and [`PROGRESS.md`](PROGRESS.md) for current status and next steps.

Planned directions include:

- Better monetary behavior rules and interior equilibria
- Dividends or other income recycling mechanisms
- Additional agent types such as government, central bank, financial institutions, wealthy households, and resource agents
- More market types such as B2B, B2C, L2B, and R2B
- Import/export flows and policy shocks
- Animated visualization of economic flows and agent interactions
- More documentation and usage examples

---

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

---

## References / Notes

- Designed for research and experimentation with macroeconomic mechanisms
- Not calibrated for any specific real-world economy
- Focuses on modularity and extensibility
- See [`docs/models.md`](docs/models.md) for how this project relates to ABM/ACE, DGE, DSGE, and equilibrium-based approaches
