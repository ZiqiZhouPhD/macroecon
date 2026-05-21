# Macroeconomic Agent-Based Simulation Sandbox

A modular, agent-based macroeconomic simulation framework designed to study
emergent macro dynamics from micro-level behavioral rules.

The project currently contains two working example economies:

- `experiments/barter_economy.py`: the original moneyless baseline, where one household and one firm barter labor for consumption goods.
- `experiments/monetary_economy.py`: a monetary extension, where labor and goods trade through money, agents hold cash, firm productivity depends on real liquidity, and profits are recycled to the household via dividend transfers.

This is an early-stage research sandbox. The monetary model is structurally complete but its behavioral dynamics have not yet been tuned to produce a stable interior equilibrium, and several properties remain unconfirmed by the author.

---

## Current Features

- Discrete-time agent-based simulation parameterized by `dt` (economic periods per step)
- Household and firm agent types with optional cash holdings
- Backward-compatible barter market
- Monetary market settlement through cash payments
- Optional nonnegative-cash constraint at the agent level
- Behavioral logic separated from agent state
- Real-balance calculations: cash influences decisions only after conversion to goods-equivalent purchasing power (`real_cash = cash / previous_goods_price`)
- Firm joint wage/price optimization via full Nelder-Mead (reflect, expand, outside contract, inside contract, shrink) in a stateful one-evaluation-per-step design
- Liquidity-dependent firm productivity (saturating function of real cash)
- Log-ratio dividend recycling from firm to household
- Rate-based time integration: all logic sets rates; `dt` appears only at transaction sites
- CSV output and matplotlib visualization
- Standard-library test suite (57 tests) under `tests/`

---

## Code Structure

```text
src/
  macroABM/
    __init__.py    # flat re-exports of public classes and helpers
    agent.py       # Agent, HouseHold, Firm state and cash accounting
    behavior.py    # price-quantity behavioral policies
    logic.py       # barter and monetary decision logic
    optimizer.py   # StepwiseNelderMead2D — stateful one-eval-per-step NM
    relation.py    # BarterMarket and MoneyMarket
    functions.py   # math utility classes
    utils.py       # goods-equivalent conversion helpers

experiments/
  barter_economy.py    # moneyless baseline simulation
  monetary_economy.py  # monetary simulation with cash, liquidity, dividends

tests/
  test_barter.py       # barter compatibility
  test_monetary.py     # money market, economic behavior, NM integration
  test_optimizer.py    # full NM algorithm correctness and convergence
  test_utils.py        # goods-equivalent helpers

outputs/
  figures/        # generated plots
  data/           # generated CSV files

docs/
  models.md       # comparison of ABM, DGE, DSGE, and hybrid model types

notes/
  todo.md         # planned extensions and open questions
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

The monetary extension replaces the barter relation with two money-mediated markets:

```text
labor market:   household sells labor  →  firm pays wages
goods market:   firm sells goods       →  household pays with cash
```

Both agents hold `cash`. Cash influences decisions only after conversion to real purchasing power. The simulation step sequence is:

```text
1. Reset per-step accumulators
2. Firm proposes (wage, goods price) via Nelder-Mead; computes effective productivity
3. Household sets labor supply rate and desired consumption rate
4. Labor settles: firm absorbs all labor supply (volume = rate × dt)
5. Production = realized_labor × effective_productivity
6. Goods settle: household buys min(desired × dt, production)
7. Goods profit rate = (production − sold) / dt  →  fed to Nelder-Mead
8. Dividend: transfer ∝ log(firm_cash / household_cash) × dt
9. Commit prices for next-step real-balance calculations
```

---

## Design Notes and Cautions

**Optimizer**: `scipy.optimize.minimize` cannot be used because it requires a synchronous callable, but each function evaluation costs one irreversible simulation step. `StepwiseNelderMead2D` in `optimizer.py` is therefore a custom stateful implementation. It implements the full standard algorithm, but Nelder-Mead was designed for static landscapes; its performance on this model's non-stationary profit landscape has not been characterized.

**Time-scale behavior**: the rate-based design is confirmed correct — `dt` appears only at transaction sites and all recorded series are rates. The invariance property (halving `dt` and doubling steps produces an equivalent trajectory) has been inspected and confirmed by the author.

**Equilibrium**: the monetary experiment runs without errors, but tends toward a liquidity-constrained corner where cash accumulates at the firm and output collapses. Dividend recycling partially counteracts this but interior equilibrium tuning has not been done.

---

## Planned Extensions

See [`TODO.md`](TODO.md) and [`PROGRESS.md`](PROGRESS.md) for current status and next steps.

High-priority open questions:

- Tune behavioral parameters for a stable interior equilibrium
- Evaluate NM simplex collapse over long runs on the non-stationary landscape

Longer-term directions:

- Additional agent types: government, central bank, financial institutions, wealthy households, resource agents
- More market types: B2B, B2C, L2B, R2B
- Policy shocks and comparative statics
- Animated visualization of economic flows
- Stochastic behavioral rules

---

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

---

## References / Notes

- Designed for research and experimentation with macroeconomic mechanisms
- Not calibrated for any specific real-world economy
- Focuses on modularity and extensibility
- See [`docs/models.md`](docs/models.md) for how this project relates to ABM/ACE, DGE, DSGE, and equilibrium-based approaches
