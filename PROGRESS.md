# Progress

Last updated: 2026-09-01

## Summary

The project has moved from a barter-only proof of concept to a backward-compatible framework with both barter and monetary experiments.

The barter experiment remains available as the baseline. The monetary experiment now uses a frozen-state instantaneous price solve and follows a smooth positive-cash interior trajectory. It is numerically consistent under time-step refinement but remains an uncalibrated research model.

---

## 2026-09-01

### Correct Expected-Clearing Firm Problem

The firm problem was clarified after separating its ex-ante decision from ex-post settlement:

- The firm assumes expected goods-market clearing, `desired consumption = production`.
- It maximizes real operating profit in goods, `production − (wage / goods price) × labor`.
- `production − realized consumption` is an ex-post goods imbalance, not profit.
- Nominal sales minus the wage bill changes firm cash after the decision. It is neither the objective nor a self-financing constraint.

Implemented changes:

- Candidate outcomes are evaluated against a frozen state with no settlement side effects or elapsed economic time.
- The first expected-clearing maximum is solved in log prices with constrained SLSQP. Later steps solve market clearing plus the constrained real-profit first-order condition from the previous optimum.
- Beginning-of-step cash is valued at the candidate current goods price for household real balances and the retained liquidity-productivity channel. This affects the economic state equations but does not create a cash-flow feasibility constraint.
- `Firm.step_real_profit` and `Firm.step_goods_imbalance` now distinguish the two real quantities. `step_profit_goods` and `Firm_Profit_Goods` remain deprecated compatibility aliases for the imbalance.
- The experiment records offered and actually matched labor separately and compares predicted real profit with the realized real operating-profit rate.
- The prior `StepwiseNelderMead2D` path remains available through `price_optimization_mode = 'stepwise'`, including floor/age restarts and the small 0.1% initial probes.

Validation of `outputs/data/monetary_economy_20260901_075516.csv`:

- All 50,000 frozen-state solves converged; the first used `expected_clearing_slsqp`, and 49,999 used `expected_clearing_foc` tracking.
- Maximum expected-consumption/production gap: `6.79e-13`.
- Maximum ex-post goods imbalance: `3.47e-15`.
- Maximum predicted-versus-realized real-profit error: `6.66e-16`.
- Cash conservation error: `1.72e-13`; production-identity error: `4.44e-16`.
- Largest recorded one-step changes were `1.88e-5` for wage, `6.53e-5` for goods price, and `1.17e-5` for real wage, all near the first step rather than as mid-run jumps.
- Household cash remained at least `1.4445`; firm cash remained at least `5.0006`; the affordability fallback did not activate.
- The focused time-refinement test converges, and 21 tested cash/initial-price combinations all returned clearing solutions. Nearly cashless-household cases can select the configured price floor and are boundary rather than interior solutions.

### Dynamic-System Qualification

The monetary model is a piecewise-smooth differential-algebraic system. Cash balances are differential states integrated through `rate × dt`; expected-clearing prices and behavioral rates are algebraic functions of the current state. The default path remains on a regular algebraic branch and is smooth. Affordability, `min`/`max`, and configured price bounds still define possible boundary regimes.

---

## 2026-05-20

*Historical implementation record. The sequential monetary pricing path described below was superseded by the frozen-state hybrid solver on 2026-09-01; `StepwiseNelderMead2D` remains available as a compatibility mode.*

### Time-Unit Cleanup

Enforced a strict separation between stocks, rates, and per-step transaction amounts:

- **Stocks** (`cash`, `price`, `wage`): no time units; used as-is.
- **Rates** (labor supply, desired consumption, production, profit, dividend): set by logic; recorded in output series.
- **Per-step amounts** (transaction volumes): `rate × dt`; computed only at the three transaction sites (labor market, goods market, dividend transfer).

Consequences:
- `dt` is no longer passed into `MonetaryHouseHoldLogic`. The affordability cap that previously required `dt` inside the logic was removed; the money market's `max_payment` cap (enforced at transaction time when `forbid_negative_cash=True`) provides equivalent protection.
- All recorded series (`list_labor`, `list_consumption`, `list_production`, `list_firm_profit`, `list_firm_profit_goods`, `list_dividends`) now store rates, not per-step amounts (`/ dt` where needed).
- `firm.logic.record_profit()` now receives the goods profit **rate** (`goods_profit / dt`) so the NM objective is dt-independent.

The resulting time-scale behavior — that halving `dt` and doubling the number of steps produces an equivalent trajectory — has been visually inspected and confirmed by the author.

### Nelder-Mead Extracted to `optimizer.py`

The firm's pricing optimizer was a bespoke, incomplete Nelder-Mead state machine embedded in `MonetaryFirmLogic`. It was extracted into a standalone module and completed.

**Why scipy cannot be used**: `scipy.optimize.minimize(method='Nelder-Mead')` calls the objective function synchronously as many times as needed per iteration. In this ABM each function evaluation costs one irreversible simulation step — the market settles, cash moves, and prices commit. A stateful, one-evaluation-per-step implementation is therefore necessary.

**New module**: `src/macroABM/optimizer.py` — `StepwiseNelderMead2D`

- Public API: `advance(observed_value) -> (x, y)` and `best` property.
- Initialization: three seed points evaluated over three calls; reflect proposed on the fourth.
- Implemented operations: reflect, expand (γ=2), outside contraction (β=0.5), inside contraction (β=0.5), two-step shrink (δ=0.5).
- Old implementation had only reflect and inside contraction (called "contract"); expand and shrink were missing.
- Lower bounds enforced by clamping at every proposal site.
- Optional dynamic tracking mode records each vertex's evaluation age. A minimum simplex radius or maximum vertex age triggers a rotated regular-simplex restart around the latest operating point and discards all stale scores.
- Optional log coordinates make the restart radius proportional for positive variables. Classical linear-coordinate behavior remains the default for compatibility.

**`MonetaryFirmLogic` after extraction**: ~35 lines, zero NM internals. The firm lazily constructs a `StepwiseNelderMead2D` on the first `update_prices()` call (seeded from current market prices), then delegates each step to `nm.advance()`.

**Dynamic tracking configuration**:

- `MonetaryFirmLogic` uses log-coordinate geometry with `nm_min_log_size = 3e-5` (approximately 0.003%) and `nm_max_vertex_age = 20`. A full-horizon parameter sweep showed that the original 0.02 trial floor dominated the `dt=0.001` dynamics and drove goods profit to zero; `3e-5` retained persistent exploration while closely matching the stable pre-restart trajectory.
- A floor restart prevents permanent refinement below the useful exploration scale; an age restart prevents an old observation from remaining the incumbent indefinitely.
- After the initial coarse search, `nm_max_log_step = 1e-3` caps each tracking proposal at approximately 0.1% log-distance from the just-evaluated point. This removed a late expansion burst without disabling exploration.
- Monetary experiment CSVs record restart counts, events, reasons, simplex size, and oldest vertex age for diagnostics.
- The optimizer remains a heuristic tracker of a path-dependent landscape, not a static-equilibrium solver. The floor and age parameters still require sensitivity analysis.

**Known limitation**:

- *Shrink-to-extend transition*: during a shrink sequence the algorithm does not re-examine whether extending would be more appropriate given the current landscape. The correct behavior is to loop over the existing (already-evaluated) vertices, observe any changes in their objective values, and exit the shrink phase early if the evidence points outward (extending) rather than inward (contracting). Skipping this check causes sporadic contraction that ignores outward-pointing information already present in the simplex.

### Test Suite Update

Added `tests/test_optimizer.py` (39 tests) covering:

- Initialisation: seed proposals, reflect-phase transition.
- All four reflect-branch decisions: accept, expand, outside contract, inside contract.
- Expand: accepted when better than reflect; rejected (reflect accepted) otherwise.
- Outside contraction: accepted when ≥ reflect; rejected triggers shrink.
- Inside contraction: accepted when better than worst; rejected triggers shrink.
- Shrink: two-step sequence (shrink vertex 1, then vertex 2), both applied on completion.
- Lower bound enforcement over 60 steps.
- Dynamic tracking: opt-in compatibility, log-coordinate conversion, floor restarts, stale-score removal, maximum vertex age, and tracking-step limits.
- Convergence to the maximum of a known 2D quadratic (places=1 within 500 evaluations).

Total tests: **66** (was 26 before this session).

---

## 2026-05-19

*Historical design record. The goods-residual objective and one-evaluation-per-step monetary default described below were superseded on 2026-09-01.*

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

Household monetary accumulators:

- `cash`, `step_money`, `step_wage_income`, `step_consumption_spending`, `step_desired_consumption`

Firm monetary accumulators:

- `cash`, `step_money`, `step_wage_bill`, `step_sales_revenue`, `step_profit`, `step_profit_goods`, `step_effective_productivity`, `step_labor_demand`

### Money Market

Added `MoneyMarket` in `src/macroABM/relation.py`.

Supports: item-for-money settlement, current and previous price tracking, short-side matching, buyer affordability capping when negative cash is forbidden.

### Monetary Logic

- `MonetaryHouseHoldLogic`: real wage elasticity of labor supply; desired consumption from real income plus real cash buffer toward a target.
- `MonetaryFirmLogic`: effective productivity from real cash liquidity (saturating function bounded by `[0.5, 1.25] × base_productivity`); joint wage/price setting delegated to `StepwiseNelderMead2D`.

Modeling convention:

```python
real_cash = cash / previous_goods_price
```

### Optimizer

`StepwiseNelderMead2D` in `src/macroABM/optimizer.py`. Full standard Nelder-Mead for two variables, designed for one-evaluation-per-step ABM environments.

### Monetary Experiment

`experiments/monetary_economy.py`.

Parameters:

```text
dt              = 0.01   (fraction of an economic period per simulation step)
total_time      = 50.0   (economic periods)
dividend_rate   = 0.1
Household cash  = 5
Firm cash       = 5
Wage            = 1
Goods price     = 1
Negative cash forbidden
```

Outputs: timestamped CSV and a three-panel PNG plot.

### Dividend Recycling

Each step transfers cash from firm to household proportional to `dividend_rate × dt × log(firm_cash / household_cash)`. The log-ratio is positive when the firm holds more than the household and negative otherwise, creating symmetric pressure toward cash balance.

### Time-Scale Design

The simulation is parameterized by `dt` (economic periods per step) and `total_time`. All behavioral logic sets rates; `dt` appears only at transaction sites. Recorded series are rates (per economic period). Time-scale invariance (halving `dt` and doubling steps produces an equivalent trajectory) has been confirmed by the author.

### Tests

66 tests across four files using the standard `unittest` library.

```bash
python -m unittest discover -v
```

---

## Current Monetary Result

Not yet re-analyzed after the 2026-05-20 refactoring. Previous characterization:

- Early: household buys goods, firm earns profit, cash migrates toward firm, firm liquidity rises, productivity rises.
- Then: household cash approaches zero, demand collapses, goods profit falls to near zero, prices oscillate.
- Dividend recycling partially counteracts cash capture but may not be sufficient to sustain activity.

Whether the trajectory changes meaningfully with the full NM (which can now expand and shrink) has not been observed.

---

## Next Modeling Work

1. ~~**Confirm time-scale behavior**~~ — confirmed by author on 2026-05-20.
2. **Observe full NM effect**: run the experiment and inspect whether the full NM (with expand and shrink) produces more stable or more oscillatory pricing than the previous reflect-contract-only version.
3. **Interior equilibrium tuning**: adjust household propensities, dividend rate, and productivity parameters so the economy sustains activity rather than collapsing to a low-output corner.
4. **NM non-stationarity**: evaluate whether the simplex collapses over long runs and whether a periodic reset heuristic is needed.

---

## Files Added

- `experiments/monetary_economy.py`
- `src/macroABM/optimizer.py`
- `src/macroABM/utils.py`
- `tests/__init__.py`
- `tests/test_barter.py`
- `tests/test_monetary.py`
- `tests/test_optimizer.py`
- `tests/test_utils.py`
- `TODO.md`
- `PROGRESS.md`

## Core Files Modified

- `src/macroABM/agent.py`
- `src/macroABM/logic.py`
- `src/macroABM/relation.py`
- `src/macroABM/__init__.py`
- `README.md`
- `AGENTS.md`
