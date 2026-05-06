# Economic Model Types

This project is currently closest to an **agent-based macroeconomic model**:
agents carry state, apply behavioral rules, interact through market relations,
and generate aggregate dynamics from the sequence of local decisions.

The notes below compare this approach with common equilibrium-based model types
in macroeconomics.

## Agent-Based Macroeconomic Models

An agent-based macroeconomic model represents the economy as a collection of
individual agents, such as households, firms, banks, governments, and central
banks. Each agent observes part of the economic state, applies a decision rule,
and interacts with other agents through explicit market mechanisms.

In this project, the current example is a simple barter economy:

- a household supplies labor and demands consumption goods
- a firm buys labor and supplies consumption goods
- a barter market executes the exchange
- prices, quantities, production, and dividends evolve over discrete time steps

The usual simulation loop is procedural:

```text
state at t
-> agents observe prices and local state
-> agents update desired prices and quantities
-> markets execute feasible transactions
-> agents update production, income, inventories, wealth, or other state
-> move to t + 1
```

### Market Clearing in Agent-Based Models

In an agent-based model, market clearing can be represented as a mechanism
rather than imposed only as an equation. For example:

```text
firms post prices
households submit demand
firms sell from available supply
unsatisfied buyers are rationed
firms adjust prices based on excess demand or inventory
production adjusts in the next period
```

If the adjustment process is fast, stable, and frictionless, the simulated
market may converge toward a classical market-clearing outcome. But the model
does not have to clear every market in every period. It can naturally allow
unsold inventory, unemployment, rationing, failed trades, bankruptcies, credit
constraints, and other disequilibrium states.

### Advantages

- Represents decentralized decision making directly.
- Handles heterogeneous agents naturally.
- Makes institutions and market mechanisms explicit.
- Can model disequilibrium paths, rationing, inventories, defaults, and
  adjustment frictions.
- Scales conceptually to many interacting sectors without requiring one global
  equilibrium system to be solved at every step.
- Useful for studying emergence, path dependence, nonlinear dynamics, and
  distributional outcomes.

### Shortcomings

- Results often depend on behavioral rules, calibration, and initialization.
- Analytical solutions are usually unavailable.
- Many simulation runs may be needed for sensitivity analysis.
- Equilibrium, welfare, and optimality concepts can be less clean than in
  standard general equilibrium models.
- Local rules must be chosen carefully to avoid arbitrary dynamics.

## Static General Equilibrium Models

A static general equilibrium model describes an economy at one point in time.
Households, firms, and other agents make choices, and prices adjust so that
markets clear simultaneously.

The core idea is:

```text
find prices such that supply equals demand in all markets
```

There is no explicit time path. The model compares one internally consistent
allocation to another.

### Advantages

- Clear definition of equilibrium.
- Useful for studying resource allocation across many markets.
- Often easier to analyze than dynamic models.
- Provides a disciplined benchmark for price and quantity consistency.

### Shortcomings

- No explicit adjustment process.
- No dynamics, expectations, accumulation, or transition path.
- Usually abstracts away failed trades, rationing, inventories, and search.
- Can hide the institutional mechanism by which markets actually coordinate.

## Dynamic General Equilibrium Models

A dynamic general equilibrium model, or **DGE model**, extends general
equilibrium across time. Agents make decisions today while accounting for future
consequences. Capital accumulation, savings, debt, production, and policy can
all evolve over time.

A deterministic DGE model has no random shocks. Its time dependence is fully
specified by initial conditions, equations, policy paths, and exogenous
parameter paths.

For example, a deterministic parameter path might be:

```text
productivity_t = 1.0 + 0.01 * t
tax_rate_t = 0.20 before year 10, then 0.25 after year 10
```

This is dynamic, but not stochastic.

### Advantages

- Captures intertemporal choices such as consumption versus saving.
- Provides a coherent equilibrium path across time.
- Useful for studying policy transitions, capital accumulation, and long-run
  adjustment.
- More structured than a purely rule-based simulation.

### Shortcomings

- Market clearing is usually imposed by solving a system of equations.
- High-dimensional economies can create difficult nonlinear fixed-point
  problems.
- The model may abstract away the actual process by which agents find prices
  and counterparties.
- Heterogeneity and institutional detail can make the solver hard to design,
  debug, and interpret.

## Dynamic Stochastic General Equilibrium Models

A dynamic stochastic general equilibrium model, or **DSGE model**, is a DGE
model with random shocks. These shocks may affect productivity, preferences,
monetary policy, fiscal policy, demand, financial conditions, or other parts of
the economy.

The common structure is:

```text
households maximize expected lifetime utility
firms maximize expected profits
policy follows specified rules
markets clear
random shocks move the economy over time
```

A typical shock process might be:

```text
A_t = rho * A_{t-1} + epsilon_t
```

where `epsilon_t` is random.

### Advantages

- Gives a disciplined framework for expectations and uncertainty.
- Can produce impulse response functions after shocks.
- Widely used in modern macroeconomics and policy analysis.
- Provides a clear connection between microeconomic optimization and aggregate
  dynamics.

### Shortcomings

- Often requires strong assumptions about optimization, expectations, and
  market clearing.
- Solving the model can be technically difficult, especially with nonlinearities
  and heterogeneous agents.
- The equilibrium solver may become high dimensional when many markets and
  constraints are included.
- Institutional details of price setting, matching, bargaining, rationing, and
  failed trades are often abstracted away.
- Representative-agent or near-representative-agent versions can miss important
  distributional and network effects.

## Agent-Based DGE Hybrids

An agent-based DGE hybrid represents agents individually, but may still impose
some equilibrium conditions inside each period. For example, households and
firms can be modeled as separate agents, while a labor market solver computes
the wage that clears aggregate labor supply and demand.

This creates a spectrum:

```text
pure equilibrium model:
    solve directly for the cleared fixed point

agent-based disequilibrium model:
    simulate local adjustment and allow markets not to clear

agent-based DGE hybrid:
    represent agents individually, but clear selected markets by solving
    equilibrium conditions
```

### Advantages

- Combines heterogeneity with some equilibrium discipline.
- Allows selected markets to clear exactly while others adjust procedurally.
- Can be useful when some markets are well approximated by fast clearing and
  others are institutionally detailed or frictional.

### Shortcomings

- Can inherit complexity from both approaches.
- Requires clear choices about which markets clear by equation and which clear
  by simulated mechanism.
- May become difficult to interpret if equilibrium solvers and behavioral rules
  interact in inconsistent ways.

## Equilibrium Solving Versus Market Mechanisms

Market clearing and equilibrium solving are related, but they are not the same
concept.

Market clearing is an economic condition:

```text
quantity supplied = quantity demanded
```

Equilibrium solving is one way to impose that condition. The model searches for
a price and allocation vector that makes all agents' plans mutually consistent.

Agent-based modeling can instead simulate the mechanism by which markets may
approach clearing:

```text
local decisions -> orders -> transactions -> rationing or inventory
-> price adjustment -> future decisions
```

In a mathematical limit with many agents, perfect information, stable
adjustment, no frictions, and fast price movement, an agent-based adjustment
process may converge to the same allocation that an equilibrium solver computes
directly. But outside that limit, the two approaches can produce meaningfully
different dynamics.

The distinction can be summarized as:

```text
general equilibrium models:
    global consistency first, mechanism abstracted

agent-based models:
    local mechanism first, global consistency emergent or approximate
```

## Position of This Project

The current implementation is best described as an early-stage
**agent-based macroeconomic simulation framework**, or **macroeconomic ABM**.
In the agent-based computational economics literature, it also fits under
**ACE**, meaning **agent-based computational economics**.

The current barter economy is not yet a DGE or DSGE model because it does not
solve for a full intertemporal general equilibrium and does not include random
shocks. It is closer to a deterministic agent-based barter economy with
behavioral price and quantity adjustment.

A concise description for this repository is:

```text
A deterministic agent-based macroeconomic simulation framework for studying
emergent aggregate dynamics from local household, firm, and market behavior.
```
