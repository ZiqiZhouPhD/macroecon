# TODO

Last updated: 2026-05-25

---

## Immediate — Inspect and Tune

- [ ] **Interior equilibrium tuning**: adjust `propensity_income`, `propensity_wealth`, `target_real_cash`, `dividend_rate`, and the liquidity factor bounds so the economy sustains a stable interior equilibrium rather than collapsing to the zero-cash corner.
- [ ] **NM simplex collapse**: after a long run (total_time ≥ 200), inspect whether the simplex diameter collapses to near zero. If so, prices freeze and the optimizer has stopped exploring.
- [ ] **Inspect full-NM effect**: compare the pricing trajectory to the previous reflect-contract-only version. Does expand/shrink improve stability or introduce more oscillation?

---

## Near-Term

- [ ] **NM shrink stopping criterion**: add a resolution threshold to `StepwiseNelderMead2D` so the shrink phase halts once the simplex diameter falls below a minimum size (e.g., `ε` on each axis). Without this, successive shrinks in a dynamical system collapse the simplex to a degenerate point and the optimizer stops exploring entirely.
- [ ] **NM shrink-to-extend transition**: during a shrink sequence, loop over the existing (already-evaluated) vertices and check whether any updated objective value suggests outward movement is warranted. If the best observed direction is extending rather than contracting, exit the shrink phase early. This prevents sporadic behavior where the optimizer keeps contracting while the landscape has shifted outward.
- [ ] **NM reset heuristic**: add an optional periodic simplex reinitialization to `StepwiseNelderMead2D` (e.g., reset every N steps around the current best vertex) to prevent collapse on non-stationary landscapes.
- [ ] **NM alternatives**: consider replacing Nelder-Mead with a finite-difference gradient estimate with exponential forgetting, which adapts more naturally to shifting objectives.
- [ ] **Dividend sensitivity analysis**: sweep `dividend_rate` and observe its effect on cash distribution and output level.
- [ ] **Remove `list_labor_supply` / `list_labor` redundancy**: both currently record `labor_market.supply_volume`. Differentiate once rationing is reintroduced, or drop one column.

---

## Code Quality

- [ ] **Implement stub classes**: `QuadraticFunction` and `LaurentFunction` in `functions.py` have no implemented methods.
- [ ] **Implement skeleton `Market`**: the base `Market` class in `relation.py` is incomplete.
- [ ] **Clarify `behavior.py`**: `Behavior`, `QuantityPriceBehavior`, and `TaylorQuantityPriceBehavior` are unused by the monetary experiment. Decide whether to remove, repurpose, or document them.
- [ ] **Add docstrings**: public modules lack usage examples and docstrings.

---

## Project Structure

- [ ] **Number and folder experiments**: reorganize `experiments/` so each experiment lives in its own numbered subfolder (e.g., `experiments/01_barter/`, `experiments/02_monetary/`) with the experiment script and its markdown documentation together.
- [ ] **Mirror output structure**: organize `outputs/` to mirror the experiment numbering (e.g., `outputs/01_barter/`, `outputs/02_monetary/`).

---

## Planned Extensions (Non-Blocking)

- Government agent
- Central Bank agent
- Financial Institutions agent
- Wealthy Households agent
- Resources agent
- Import/Export agent
- Firm classification: B2B, B2C, L2B, R2B
- Policy shocks and comparative statics
- Stochastic behavioral rules and Monte Carlo averaging
- Animated visualization of economic flows
