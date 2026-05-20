# Progress

Last updated: 2026-05-19

## Summary

The project has moved from a barter-only proof of concept to a backward-compatible framework with both barter and monetary experiments.

The barter experiment remains available as the baseline. A new monetary experiment introduces cash holdings, money-mediated labor and goods markets, real-balance behavior, liquidity-dependent firm productivity, no-inventory goods settlement, optional nonnegative-cash constraints, richer plotting, and tests.

The monetary model is functional, but the current behavior rules do not yet produce the desired well-balanced interior equilibrium. The present run tends toward a liquidity-constrained corner where cash accumulates at the firm and household activity collapses to a low level.

---

## 2026-05-19

Redesigned the monetary economy model and wrote full documentation in `experiments/monetary_economy.md`. No code was changed; all decisions were documented first for later implementation.

Key design decisions made:

- **Firm pricing via Nelder-Mead**: the firm jointly sets wage and goods price each round using a 2D Nelder-Mead search over (wage, goods price), optimizing real goods profit. The simplex is initialized over 3 steps at `(w0, p0)`, `(1.2·w0, p0)`, `(w0, 1.2·p0)` where `w0` and `p0` are passed from the experiment. From step 3 onward, standard Nelder-Mead iterations proceed one step per round.
- **Profit defined as real goods**: `profit = production − consumption` in physical units. This exits the economy each round with no inventory. The firm maximizes this quantity.
- **Labor market fully absorbed**: the firm takes all household labor supply with no short-side rationing.
- **Effective productivity moves to price-update stage**: computed from last step's firm cash before household volumes are set.
- **Household affordability cap**: desired consumption is capped so the household cannot go cash-negative.
- **Firm cash drain**: a dividend transfer from firm to household each step, proportional to `log(firm_cash / household_cash)`, justified by the symmetric real-world pressures of household investment and firm dividend payout.

---

## Implemented

### Monetary Agent State

`HouseHold` and `Firm` now support optional cash balances:

```python
initial_cash=...
forbid_negative_cash=True
```

The default remains backward compatible:

```python
initial_cash=0
forbid_negative_cash=False
```

Household monetary accumulators include:

- `cash`
- `step_money`
- `step_wage_income`
- `step_consumption_spending`
- `step_desired_consumption`

Firm monetary accumulators include:

- `cash`
- `step_money`
- `step_wage_bill`
- `step_sales_revenue`
- `step_profit`
- `step_effective_productivity`
- `step_labor_demand`

### Money Market

Added `MoneyMarket` in `src/macroABM/relation.py`.

It supports:

- item-for-money settlement
- current and previous price tracking
- short-side matching
- buyer affordability capping when negative cash is forbidden

### Monetary Logic

Added:

- `MonetaryHouseHoldLogic`
- `MonetaryFirmLogic`

Important modeling convention:

```python
real_cash = cash / previous_goods_price
```

Money is used as an accounting and settlement object. Behavioral logic should use money only after conversion into real purchasing power or goods-equivalent value.

### Monetary Experiment

Added `experiments/monetary_economy.py`.

Initialization:

```text
Household cash = 5
Firm cash = 5
Wage = 1
Goods price = 1
Negative cash forbidden
```

Step sequence:

```text
1. reset step accumulators
2. update prices
3. update volumes
4. match labor by short side
5. settle labor market
6. compute production from realized labor and effective productivity
7. set goods sold equal to production
8. settle goods market
9. commit prices for next-step real-balance calculations
```

### Plotting

The monetary experiment now creates a three-panel plot:

1. Nominal dynamic values: wage, goods price, firm profit.
2. Real or goods-equivalent dynamic values: real wage, labor, desired consumption, realized consumption, productivity, firm profit in goods.
3. Cash balances only: household cash, firm cash, household cash in goods, firm cash in goods.

### Utilities

Added `src/macroABM/utils.py`:

```python
goods_equivalent(nominal_value, goods_price)
goods_equivalent_series(nominal_values, goods_prices)
```

### Tests

Added standard-library `unittest` coverage under `tests/`.

Current passing test count: 21.

Coverage includes:

- barter compatibility
- barter transaction accounting
- money market settlement
- short-side matching
- no-overdraft constraints
- goods-equivalent conversion
- qualitative economic expectations:
  - higher real cash raises household desired consumption
  - higher real wage raises household labor supply
  - higher firm real cash raises effective productivity
  - behavior depends on real balances, not nominal cash alone
  - money is conserved in a one-step monetary simulation

Verification command:

```bash
python -m unittest discover -v
```

---

## Current Monetary Result

The latest monetary experiment demonstrates a liquidity bottleneck.

Early in the run:

- Household starts with enough cash to buy goods.
- Firm buys labor and sells goods.
- Firm earns positive profit.
- Cash moves from household to firm.
- Firm real liquidity rises, improving effective productivity.

Then:

- Household cash reaches the zero-cash floor.
- Firm cash reaches the whole money stock.
- Household demand becomes strongly constrained by current wage income.
- Production and consumption fall to a very low level.
- Firm profit goes to roughly zero.
- Prices oscillate near the low-activity boundary.

This is economically informative, but not the equilibrium example we want next.

---

## Next Modeling Work

Goal: adjust behavior so the monetary economy can reach a better interior equilibrium.

Likely directions:

- Add dividend payments from firm to household.
- Add a wage adjustment rule so household liquidity scarcity feeds back into labor income.
- Make firm price adjustment less oscillatory near zero demand.
- Make household saving behavior target an interior cash buffer without fully starving demand.
- Add firm payout or reinvestment logic so cash does not remain permanently trapped at the firm.

The most natural next experiment is probably dividend recycling, because it preserves the closed-economy money stock while allowing firm profits to return to households and support stable demand.

---

## Files Added

- `experiments/monetary_economy.py`
- `src/macroABM/utils.py`
- `tests/__init__.py`
- `tests/test_barter.py`
- `tests/test_monetary.py`
- `tests/test_utils.py`
- `PROGRESS.md`

## Core Files Modified

- `src/macroABM/agent.py`
- `src/macroABM/relation.py`
- `src/macroABM/logic.py`
- `src/macroABM/__init__.py`
- `README.md`
- `AGENTS.md`
