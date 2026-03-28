# CLAUDE.md — Project Guide

## What This Is

An **agent-based macroeconomic simulation framework** for studying emergent macro dynamics (prices, output, dividends) from micro-level behavioral rules. The current implementation is a minimal proof-of-concept: one household and one firm trading labor for consumption goods in a barter market.

Author: Ziqi Zhou (2026), MIT License.

---

## Project Structure

```
macroecon/
├── src/
│   └── macroABM/           # Installable package — import this, don't run it
│       ├── __init__.py     # Flat re-exports of all public classes
│       ├── agent.py        # Agent state classes (HouseHold, Firm)
│       ├── behavior.py     # Price-quantity behavioral policies
│       ├── logic.py        # Decision-making logic (LinearHouseHoldLogic, LinearFirmLogic)
│       ├── relation.py     # Market structures (BarterMarket)
│       └── functions.py    # Math utilities (LinearFunction, stubs for Quadratic/Laurent)
├── experiments/            # Runnable simulations
│   └── barter_economy.py   # Current working example; outputs CSV + PNG
├── outputs/                # Auto-created by experiments
│   ├── data/               # CSV files timestamped per run
│   └── figures/            # PNG plots
├── notes/
│   └── todo.md             # Planned extensions roadmap
├── pyproject.toml          # Package metadata and build config
└── README.md
```

---

## Architecture

The framework has four distinct layers:

### 1. Agent State (`agent.py`)
Agents hold per-step accumulators (`step_labor`, `step_consumption`, `step_production`, etc.) that are reset each timestep by `step_preprocess()`. State is mutated by `handle_transaction()` when a market settles.

- `Agent` — abstract base
- `HouseHold` — tracks consumption and labor supply
- `Firm` — tracks labor purchased, product sold, and dividends; computes `production = labor × productivity` in `step_postprocess()`

### 2. Decision Logic (`logic.py`)
Logic objects are injected into agents at construction and drive behavioral decisions. Separated from agent state intentionally so behaviors can be swapped without touching agent code.

- `LinearHouseHoldLogic` — elastic labor supply: `labor = labor_0 × (price/price_0)^(-elasticity)`, then `consumption = labor / price`
- `LinearFirmLogic` — profit-maximizing price setter using Newton's method: iteratively adjusts price toward MR = MC

### 3. Market Relations (`relation.py`)
Markets mediate transactions between agents. `BarterMarket` holds two agents and two volumes; `price = volumes[0] / volumes[1]`. `handle_transactions()` executes swaps and calls each agent's `handle_transaction()`.

### 4. Behavioral Policies (`behavior.py`)
`TaylorQuantityPriceBehavior` encodes a Taylor-expanded price-quantity curve around a reference point. Used as a building block for more complex demand/supply schedules.

---

## Simulation Loop (per timestep)

```
1. step_preprocess()       — reset all per-step accumulators on all agents
2. update_prices()         — firms run Newton's method to set new price
3. update_volumes()        — agents choose quantities given current prices
4. handle_transactions()   — markets execute swaps, update agent state
5. step_postprocess()      — firms compute production and dividends
```

This order is strict. Prices move before quantities; quantities move before settlement.

---

## Installation

The framework is packaged as `macroABM` under `src/`. Install it once in editable mode from the project root:

```bash
pip install -e .
```

This lets experiments import `macroABM` directly without any `sys.path` manipulation.

For VS Code/Pylance to resolve the package, `.vscode/settings.json` sets `python.analysis.extraPaths` to `["src"]`. That file is gitignored.

---

## Running the Simulation

```bash
python experiments/barter_economy.py
```

Runs 100 timesteps, prints save paths, writes:
- `outputs/data/barter_economy_YYYYMMDD_HHMMSS.csv` — 6 columns: Step, Labor_Price, Labor_Supply, Consumption, Production, Dividends
- `outputs/figures/barter_economy.png` — time-series plot of all 5 economic variables

---

## Key Parameters (barter_economy.py)

| Parameter | Default | Meaning |
|---|---|---|
| `productivity` | 2 | Units of output per unit of labor input |
| `elasticity` | 0.2 | Household labor supply elasticity to wages |
| `market_elasticity` | -3 | Firm's assumed price sensitivity of demand |
| Initial volumes | [1, 1] | Starting labor and consumption quantities |
| Steps | 100 | Simulation length |

---

## Planned Extensions (notes/todo.md)

- Docstrings and usage examples throughout `src/`
- Money/currency layer; firm liquidity tracking
- Additional agent types: Government, Central Bank, financial institutions, wealthy households, resource agents
- Firm market types: B2B, B2C, L2B (labor-to-business), R2B (resource-to-business)
- Import/export flows

When adding new agent types, follow the pattern: subclass `Agent`, inject a `Logic` object, register markets via `mount_relation()`.

---

## Dependencies

Declared in `pyproject.toml`:
- `matplotlib` — plotting
- `pandas` — CSV export

Standard library: `os`, `datetime`.

---

## What to Watch Out For

- `functions.py` has stub classes (`QuadraticFunction`, `LaurentFunction`) with no implemented methods — don't rely on them yet.
- The `Market` class in `relation.py` is an incomplete skeleton; use `BarterMarket` instead.
- No stochasticity — the model is fully deterministic given initial conditions.
- No validation for economically degenerate states (negative prices, zero labor, etc.).
