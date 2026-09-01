# TODO

Last updated: 2026-09-01

---

## Immediate — Inspect and Tune

- [ ] **Economic calibration**: adjust `propensity_income`, `propensity_wealth`, `target_real_cash`, `dividend_rate`, and liquidity parameters against explicit calibration targets. The current default is numerically stable but leaves most cash at the firm.
- [ ] **Firm shutdown/labor demand**: add an explicit choice not to hire all offered labor for cases where the affordability fallback becomes active.
- [ ] **Boundary-regime analysis**: map the cash/parameter region over which the expected-clearing price solution is interior and locally unique rather than lying on the configured price floor.

---

## Near-Term

- [x] **NM shrink stopping criterion**: optional simplex-floor restarts now prevent permanent collapse in `StepwiseNelderMead2D`.
- [ ] **NM shrink-to-extend transition**: during a shrink sequence, loop over the existing (already-evaluated) vertices and check whether any updated objective value suggests outward movement is warranted. If the best observed direction is extending rather than contracting, exit the shrink phase early. This prevents sporadic behavior where the optimizer keeps contracting while the landscape has shifted outward.
- [x] **NM reset heuristic**: floor and vertex-age triggers rebuild a rotated regular simplex and discard stale scores.
- [x] **Separate solver time from economic time**: the default monetary price problem is solved against a frozen state, with constrained initialization and first-order tracking. The sequential Nelder-Mead tracker remains an optional compatibility mode.
- [ ] **Dividend sensitivity analysis**: sweep `dividend_rate` and observe its effect on cash distribution and output level.
- [x] **Differentiate labor supply and matched labor output**: `Labor_Supply` records the offered rate while `Labor` records realized firm labor per unit time.

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
