# AGENTS.md - Project Guide

## What This Is

An agent-based macroeconomic simulation framework for studying emergent macro dynamics from micro-level behavioral rules.

The project now has two working example paths:

- A moneyless barter baseline.
- A monetary extension with cash balances, money-mediated markets, real-balance behavior, and optional nonnegative-cash constraints.

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
      relation.py     # BarterMarket and MoneyMarket
      functions.py    # math utilities
      utils.py        # goods-equivalent conversion helpers
  experiments/
    barter_economy.py
    monetary_economy.py
  tests/
    test_barter.py
    test_monetary.py
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

The framework has four main layers.

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

- `MonetaryHouseHoldLogic`: chooses labor supply from real wage and desired consumption from real income plus real cash buffer.
- `MonetaryFirmLogic`: sets wage/goods price and uses real cash liquidity to determine effective productivity.

Important modeling rule: money should not directly influence decisions as a nominal number. Convert it to goods-equivalent purchasing power first:

```python
real_cash = cash / previous_goods_price
```

### 3. Market Relations (`relation.py`)

Markets mediate transactions between agents.

- `BarterMarket`: preserves the original moneyless barter experiment.
- `MoneyMarket`: settles item-for-money transactions, tracks current and previous prices, supports short-side matching, and caps purchases when the buyer cannot overdraft.

For labor matching in the monetary experiment:

```python
realized_labor = min(labor_supply, labor_demand)
```

For goods in the current no-inventory experiment:

```python
goods_sold = firm_production
```

### 4. Utilities (`utils.py`)

Helpers for converting nominal values into equivalent goods amounts:

```python
goods_equivalent(nominal_value, goods_price)
goods_equivalent_series(nominal_values, goods_prices)
```

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
1. step_preprocess()
2. update_prices()
3. update_volumes()
4. match labor by the short side
5. settle labor market
6. firm computes production from realized labor and effective productivity
7. goods sold equals production
8. settle goods market
9. commit current prices as previous prices for next-step real-balance calculations
```

Run:

```bash
python experiments/monetary_economy.py
```

The monetary experiment writes a CSV and a three-panel plot:

- nominal dynamic values
- real/goods-equivalent dynamic values
- cash balances separated from other dynamics

---

## Tests

Run:

```bash
python -m unittest discover -v
```

The tests cover:

- barter transaction compatibility
- money market settlement and cash accounting
- short-side matching
- no-overdraft enforcement
- goods-equivalent conversion helpers
- qualitative economic expectations, including real-balance behavior and liquidity-driven productivity

---

## Current Status and Modeling Caution

The monetary experiment is functional, but not yet a polished equilibrium example.

With the current behavior rules, the firm earns profits early, cash migrates from household to firm, the household reaches the zero-cash constraint, and the system falls into a low-activity liquidity-constrained corner. This is a useful diagnostic result, but the next modeling step is to adjust behavior or income recycling so the economy can reach a better interior equilibrium.

See `PROGRESS.md` for the current work log.

---

## What to Watch Out For

- Keep `BarterMarket` and the barter experiment backward compatible.
- Use `MoneyMarket` for monetary experiments instead of modifying barter settlement.
- Convert cash to goods-equivalent purchasing power before using it in behavior logic.
- The current monetary model has no inventory.
- The current monetary model has no dividends or transfers, so money can become trapped with the firm.
- `functions.py` has stub classes (`QuadraticFunction`, `LaurentFunction`) with no implemented methods.
- The skeleton `Market` class is incomplete; use `BarterMarket` or `MoneyMarket`.
- No stochasticity yet.
