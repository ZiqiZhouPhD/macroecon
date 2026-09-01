# Macroeconomic Agent-Based Simulation Sandbox

A modular, agent-based macroeconomic simulation framework designed to study
emergent macro dynamics from micro-level behavioral rules.

The project currently contains two working example economies:

- `experiments/barter_economy.py`: the original moneyless baseline, where one household and one firm barter labor for consumption goods.
- `experiments/monetary_economy.py`: a monetary extension, where labor and goods trade through money, agents hold cash, firm productivity depends on real liquidity, and profits are recycled to the household via dividend transfers.

This is an early-stage research sandbox. The default monetary example now follows a smooth interior trajectory and passes time-step refinement checks, but it is not yet a calibrated macroeconomic model.

---

## Current Features

- Discrete-time agent-based simulation parameterized by `dt` (economic periods per step)
- Household and firm agent types with optional cash holdings
- Backward-compatible barter market
- Monetary market settlement through cash payments
- Optional nonnegative-cash constraint at the agent level
- Behavioral logic separated from agent state
- Real-balance calculations: beginning-of-step cash is valued at the candidate current goods price (`real_cash = cash / goods_price`)
- Instantaneous firm wage/price optimization against a frozen economic state: constrained initialization plus first-order tracking of the expected-clearing optimum
- Compatible `StepwiseNelderMead2D` with floor/age restarts for genuinely sequential objectives
- Liquidity-dependent firm productivity (saturating function of real cash)
- Log-ratio dividend recycling from firm to household
- Rate-based time integration: all logic sets rates; `dt` appears only at transaction sites
- CSV output and matplotlib visualization
- Standard-library test suite (75 tests) under `tests/`

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
2. Firm maximizes expected real profit, assuming desired consumption equals production
3. Household sets labor supply rate and desired consumption rate
4. Labor settles: firm absorbs all labor supply (volume = rate × dt)
5. Production = realized_labor × effective_productivity
6. Goods settle: household buys min(desired × dt, production)
7. Record real and nominal operating profit; retain production − sold as an ex-post imbalance
8. Dividend: transfer ∝ log(firm_cash / household_cash) × dt
9. Commit prices for next-step real-balance calculations
```

---

## Design Notes and Cautions

**Firm objective and optimizer**: at a candidate wage `w` and goods price `p`, the firm assumes its production is sold and maximizes expected real operating profit `production − (w/p) × labor`, subject to expected household consumption equalling production. Cash settlement is not an objective or self-financing constraint. Candidate evaluations are side-effect free and do not advance time. The first frozen-state problem is solved with constrained SLSQP; subsequent steps track market clearing and the constrained first-order condition from the previous optimum. The former one-evaluation-per-step Nelder-Mead implementation remains available through `price_optimization_mode = 'stepwise'`, including its floor, vertex-age, and proposal-step safeguards.

**Time-scale behavior**: `dt` appears only at transaction sites and all recorded series are rates. Refinement at `dt = 0.002`, `0.001`, `0.0005`, and `0.00025` shows decreasing errors against the finest trajectory. Solver evaluations no longer count as elapsed economic time.

**Dynamic-system qualification**: the monetary model is best described as a differential-algebraic, piecewise-smooth system: cash stocks are Euler-integrated differential states, while optimal prices and behavioral rates are algebraic functions of the current state. The default interior branch is continuous. Hard affordability caps and configured price bounds can still create boundary regimes for extreme states.

**Current result**: over 50 periods, all 50,000 price solves converge. Expected consumption and production differ by at most `6.8e-13`; the ex-post goods imbalance is below `3.5e-15`; cash conservation and the real-profit identity hold to machine precision. Both cash balances remain positive and all displayed trajectories are smooth. The firm accumulates most cash, so behavioral calibration and distributional realism remain open questions.

---

## Planned Extensions

See [`TODO.md`](TODO.md) and [`PROGRESS.md`](PROGRESS.md) for current status and next steps.

High-priority open questions:

- Calibrate household, dividend, and liquidity parameters
- Analyze price-floor and affordability regimes under extreme cash distributions

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
