# Macroeconomic Agent-Based Simulation Sandbox

A modular, agent-based macroeconomic simulation framework designed to study **emergent dynamics from micro-level behaviors**.  
This repository provides an early-stage implementation of a flexible macroeconomic sandbox, enabling experimentation with heterogeneous agents, markets, and behavioral rules.

> Note: This is an early-stage version. Future extensions will include additional agent types, monetary features, and more complex market interactions. The simulation is fully functional in its current form.

---

## Current Features

- **Discrete-time agent-based simulation**
- **Heterogeneous agents** (Households and Firms)
- **Simple barter market** connecting labor and consumption
- **Behavioral rules and decision logic** separated from agent state
- **Simulation loop** with stepwise update: preprocessing → price update → volume update → transactions → postprocessing
- **Data recording and visualization** using matplotlib

The current minimal experiment is located in `experiments/barter_economy.py`.

---

## Code Structure

```

src/
agent.py        # agent definitions and state variables
behavior.py     # decision rules and behavioral policies
relations.py    # interaction structures between agents
logic.py        # simulation loop and stepwise dynamics
functions.py    # utility and helper functions

experiments/
barter_economy.py  # runnable simulation example
outputs/
figures/        # generated plots
data/           # simulation results

notes/
todo.md         # planned extensions and future improvements

````

---

## Getting Started

1. Clone the repository:

```bash
git clone https://github.com/ZiqiZhouPhD/macroecon.git
cd macroecon
```

2. Run the example simulation:

```bash
python experiments/barter_economy.py
```

Simulation outputs (figures and data) are saved to the `outputs/` folder.

2. Modify parameters for alternative use cases.

---

## Planned Extensions

See [`notes/todo.md`](notes/todo.md) for planned enhancements, including:

* Introduction of currency and liquidity tracking
* Additional agent types (government, central bank, financial institutions, wealthy households)
* Firm classification and more complex market interactions
* Import/export flows and policy shocks
* Enhanced documentation and modularization for large-scale experiments

These extensions are non-blocking; the current framework remains fully functional.

---

## License

This project is released under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## References / Notes

* Designed for research and experimentation with macroeconomic mechanisms
* Not (yet) calibrated for any specific real-world economy
* Focuses on **modularity and extensibility** for future studies