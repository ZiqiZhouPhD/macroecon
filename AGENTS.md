# AGENTS.md - Project Guide

## What This Is

An agent-based macroeconomic simulation framework for studying emergent macro dynamics from micro-level behavioral rules.

The project currently has two working example paths:

- A moneyless barter baseline.
- A monetary extension with cash balances, money-mediated markets, real-balance behavior, liquidity-dependent firm productivity, and log-ratio dividend recycling.

Author: Ziqi Zhou (2026), MIT License.

---

## Project Structure

```text
macroecon/
  src/
    macroABM/
      __init__.py     # flat re-exports of public classes/helpers
      agent.py        # Agent, HouseHold, Firm state and cash accounting
      behavior.py     # price-quantity behavioral policies
      logic.py        # barter and monetary decision logic
      optimizer.py    # StepwiseNelderMead2D — stateful one-eval-per-step NM
      relation.py     # BarterMarket and MoneyMarket
      functions.py    # math utilities
      utils.py        # goods-equivalent conversion helpers
  experiments/
    barter_economy.py
    monetary_economy.py
  tests/
    test_barter.py
    test_monetary.py
    test_optimizer.py
    test_utils.py
  outputs/
    data/
    figures/
  docs/
    models.md
  notes/
    todo.md
  PROGRESS.md
  README.md
  pyproject.toml
```

---

## Architecture

The framework has five main layers.

For economic model terminology and tradeoffs, see `docs/models.md`. It explains how this project relates to agent-based computational economics, DGE, DSGE, and equilibrium-solving approaches.

### 1. Agent State (`agent.py`)

Agents hold per-step accumulators that are reset each timestep by `step_preprocess()`. State is mutated by `handle_transaction()` when a market settles.

- `Agent`: abstract base with relation mounting, update delegation, and optional cash constraints.
- `HouseHold`: tracks consumption, labor, cash, wage income, spending, and desired consumption.
- `Firm`: tracks labor, product sold, production, cash, wage bill, sales revenue, profit, and effective productivity.

Agents accept:

```python
forbid_negative_cash=True
```

When enabled, direct cash overdrafts raise an error. Money markets also cap transaction volumes to keep constrained buyers from going negative.

### 2. Decision Logic (`logic.py`)

Logic objects are injected into agents at construction and drive behavioral decisions. This separation is intentional so behavior can be swapped without changing agent state classes.

Barter logic:

- `LinearHouseHoldLogic`: elastic labor/consumption choice using the barter relative price.
- `LinearFirmLogic`: price adjustment using Newton's method.

Monetary logic:

- `MonetaryHouseHoldLogic`: chooses labor supply from real wage and desired consumption from real income plus a real cash buffer gap toward a target.
- `MonetaryFirmLogic`: sets wage and goods price jointly via Nelder-Mead and uses real cash liquidity to determine effective productivity.

Important modeling rule: money must not influence decisions as a nominal number. Convert it first:

```python
real_cash = cash / previous_goods_price
```

### 3. Optimizer (`optimizer.py`)

`StepwiseNelderMead2D` implements the full standard Nelder-Mead algorithm (Nelder & Mead 1965) for two variables. It is designed for sequential environments where exactly one function evaluation is available per simulation step.

```python
nm = StepwiseNelderMead2D(seeds=[(w0, p0), (w0*1.2, p0), (w0, p0*1.2)])
x, y = nm.advance(None)       # first call: no prior value
# ... run one step, observe value ...
x, y = nm.advance(value)      # subsequent calls: feed back last observation
```

Operations implemented: reflect, expand, outside contraction, inside contraction, two-step shrink.

Scipy's `scipy.optimize.minimize` cannot be used here because it requires a synchronous callable, but in this ABM each function evaluation costs one irreversible simulation step.

**Known limitation**: Nelder-Mead stores profit values from past steps and trusts them as a fixed landscape. In this model the landscape shifts each step as cash balances change. The simplex may collapse or track a stale optimum. A periodic reset heuristic or a different optimizer may improve long-run tracking.

### 4. Market Relations (`relation.py`)

Markets mediate transactions between agents.

- `BarterMarket`: preserves the original moneyless barter experiment.
- `MoneyMarket`: settles item-for-money transactions, tracks current and previous prices, supports short-side matching, and caps purchases when the buyer cannot overdraft.

### 5. Utilities (`utils.py`)

Helpers for converting nominal values into equivalent goods amounts:

```python
goods_equivalent(nominal_value, goods_price)
goods_equivalent_series(nominal_values, goods_prices)
```

---

## Time-Unit Discipline

All behavioral quantities are rates (per unit time), not per-step amounts.

| Kind | Examples | Rule |
|---|---|---|
| Stocks | `cash`, `price`, `wage` | No time units; use as-is |
| Rates | `labor_supply`, `desired_consumption`, `production` | Per economic period; set by logic |
| Per-step | transaction volumes | Rate × dt; created only at the transaction site |

The parameter `dt` (fraction of an economic period per simulation step) appears in **exactly three places**: the labor transaction, the goods transaction, and the dividend transfer. It does not appear in any logic or behavior code.

Recorded series (`list_labor`, `list_consumption`, `list_production`, etc.) store rates, not per-step amounts.

The time-scale invariance property — that halving `dt` and doubling the number of steps produces an equivalent trajectory — has been inspected and confirmed by the author.

---

## Simulation Loops

### Barter Experiment

```text
1. step_preprocess()
2. update_prices()
3. update_volumes()
4. handle_transactions()
5. step_postprocess()
```

Run:

```bash
python experiments/barter_economy.py
```

### Monetary Experiment

```text
1.  step_preprocess()
2.  update_prices()   — firm proposes (wage, goods price) via NM; computes effective productivity
3.  update_volumes()  — household sets labor supply rate and desired consumption rate
4.  labor_market.volume = supply_rate × dt  (firm absorbs all; no short-side rationing)
5.  settle labor market
6.  production = realized_labor × effective_productivity
7.  goods_market.volume = min(desired_consumption × dt, production)  (demand-determined)
8.  settle goods market
9.  goods_profit_rate = (production − goods_sold) / dt  → recorded and fed to NM
10. dividend: firm → household, proportional to log(firm_cash / household_cash) × dt
11. commit prices  (previous_price ← price, for next-step real-balance calculations)
```

Run:

```bash
python experiments/monetary_economy.py
```

The monetary experiment writes a timestamped CSV and a three-panel plot:

- Panel 1: nominal rates — wage, goods price, firm nominal profit
- Panel 2: real/goods-equivalent rates — real wage, labor, desired and realized consumption, productivity, goods profit
- Panel 3: cash stocks — household cash, firm cash, dividend rate

---

## Tests

Run:

```bash
python -m unittest discover -v
```

Current test count: **57** across four files.

| File | What it covers |
|---|---|
| `test_barter.py` | barter transaction compatibility |
| `test_monetary.py` | money market settlement, cash accounting, qualitative economic expectations, NM integration |
| `test_optimizer.py` | all five NM operations with exact geometry, lower-bound enforcement, convergence on a known quadratic |
| `test_utils.py` | goods-equivalent conversion helpers |

---

## Current Status and Modeling Caution

The monetary experiment is functional but not yet a validated equilibrium example.

- The firm's Nelder-Mead pricing is implemented correctly but operates on a non-stationary landscape (profit depends on current cash balances, which change each step). Convergence to a stable price pair is not guaranteed and has not been analyzed.
- Time-scale invariance (rate × dt integration) has been implemented and reviewed structurally, but the resulting trajectory has not yet been visually inspected or quantitatively confirmed by the author for different values of `dt`.
- The dividend recycling mechanism prevents permanent cash capture at the firm, but interior equilibrium tuning has not been done.

See `TODO.md` for next steps and `PROGRESS.md` for the full work log.

---

## What to Watch Out For

- Keep `BarterMarket` and the barter experiment backward compatible.
- Use `MoneyMarket` for monetary experiments instead of modifying barter settlement.
- Convert cash to goods-equivalent purchasing power before using it in behavior logic.
- The current monetary model has no inventory. Unsold goods exit the economy each step.
- The skeleton `Market` class is incomplete; use `BarterMarket` or `MoneyMarket`.
- `functions.py` has stub classes (`QuadraticFunction`, `LaurentFunction`) with no implemented methods.
- No stochasticity yet.
