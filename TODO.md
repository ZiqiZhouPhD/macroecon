# TODO

Project-level task list. Factored here from `notes/todo.md`.

---

## Implementation — Monetary Economy Redesign

Implement the model designed on 2026-05-19 and documented in `experiments/monetary_economy.md`.

- [ ] **Nelder-Mead firm pricing**: replace fixed-wage + reactive goods-price logic in `MonetaryFirmLogic.update_prices` with a 2D Nelder-Mead search over (wage, goods price). Manage the simplex state across steps (one iteration per round, not run-to-convergence). Use `scipy.optimize.minimize` with `method='Nelder-Mead'` or implement simplex steps manually.
- [ ] **Simplex initialization**: accept `wage_init` and `price_init` in the firm constructor. Seed the simplex at `(wage_init, price_init)`, `(wage_init * 1.2, price_init)`, `(wage_init, price_init * 1.2)` across the first 3 steps before iterating.
- [ ] **Real goods profit**: record `production − consumption` (physical units) as the profit signal fed back to Nelder-Mead each round.
- [ ] **Effective productivity in price-update stage**: move liquidity-factor computation from `update_volumes` to `update_prices` in `MonetaryFirmLogic`. It uses last step's ending firm cash.
- [ ] **Full labor absorption**: remove short-side matching from the labor market. The firm absorbs all household labor supply.
- [ ] **Household affordability cap**: cap desired consumption so spending cannot exceed household cash.
- [ ] **Firm cash drain**: add a per-step dividend transfer from firm to household proportional to `log(firm_cash / household_cash)`. Include a proportionality constant as a tunable parameter.
- [ ] **Update experiment loop**: align `experiments/monetary_economy.py` step sequence with the documented design (remove firm `update_volumes`, remove labor `match_short_side`, add drain step, record real goods profit).
- [ ] **Update tests**: revise `tests/test_monetary.py` to cover the new behavior rules.

---

## Refactoring — Project Structure

- [ ] **Separate figures from data**: split `outputs/` into `outputs/figures/` and `outputs/data/` if not already done, and ensure each experiment writes to the correct subfolder.
- [ ] **Number and folder experiments**: reorganize `experiments/` so each experiment lives in its own numbered subfolder, e.g. `experiments/01_barter/` and `experiments/02_monetary/`, with the experiment script and its markdown documentation together.
- [ ] **Mirror output structure**: organize `outputs/` to mirror the experiment folder numbering, e.g. `outputs/01_barter/` and `outputs/02_monetary/`, so results are unambiguously linked to their experiment.
- [ ] **Factor TODO to project root**: done — this file replaces `notes/todo.md`.

---

## Documentation

- [ ] Add docstrings and usage examples for all public modules.

---

## Planned Extensions (Non-Blocking)

From prior planning in `notes/todo.md`:

- Government agent
- Central Bank agent
- Financial Institutions agent
- Wealthy Households agent
- Resources agent
- Import/Export agent
- Firm classification: B2B, B2C, L2B, R2B
