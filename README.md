# Autonomous Decision Agent

An agent that has to act in a partially observable grid world: it cannot see hazards, only local percepts, and must rescue a target and reach the exit without dying. The project builds the agent up in three stages, from classical search to probabilistic reasoning to sequential decision-making under stochastic dynamics.

Final project for Fundamentals of Artificial Intelligence (ICAI).

## The environment

A 6x6 "palace" with hidden lethal cells (traps and an enemy soldier), a target to rescue and an exit. The agent starts at (1, 1) and, on each cell, only receives boolean percepts telling it whether each hazard is in its neighbourhood. It carries a single grenade that can eliminate the soldier.

## Approach

### Part 1 — Search and logical inference (`Parte_1/`)

- **BFS path planning** (`search_agent.py`): shortest safe path start → target → exit on the grid, with hazards as blocked cells. In `AUTO` mode the planner is given the true map, so it serves as an upper-bound baseline rather than an autonomous agent.
- **Logical hazard inference** (`kurtz.py`): from the history of percepts, every cell adjacent to a percept-free visit is marked safe; the remaining neighbours of a cell with a percept become *possible* hazards, and a hazard is *certain* when only one candidate is left. Pits and the soldier are tracked separately, since they produce different percepts. These deductions are rendered on the board to guide the player in `MANUAL` mode.

### Part 2 — Bayesian belief state (`Parte_2/bayes.py`, `palacio.py`)

- The agent keeps a probability distribution over the location of each hidden element (three traps, soldier, exit), initialised with a uniform prior over all cells except the start.
- After each percept it applies **Bayes' rule** cell by cell:
  `P(x | e) ∝ P(e | x) · P(x)`, where the likelihood is 1 if the percept is consistent with the element being at `x` (i.e. `x` is in the agent's neighbourhood and the percept was seen, or not in it and the percept was absent) and 0 otherwise. The posterior is then renormalised.
- The beliefs are combined into a **per-cell risk of death** (sum of trap and soldier probabilities) and visualised as heatmaps.
- **Risk-aware greedy policy**: each move is scored by its risk, with a hard penalty above a threshold `p = 0.2`, a bonus for unexplored cells and, once the target is rescued, a pull towards the most likely exit cell. The grenade is thrown at the adjacent cell with the highest soldier probability when the soldier is sensed.

### Part 3 — Markov Decision Process (`Parte_2/river_mdp.py`)

- A 7x6 river with a column-dependent current that pushes the agent downstream with probability equal to the current's strength, plus randomly placed islands.
- States are cells; actions are `UP, DOWN, LEFT, RIGHT, STAY`; rewards are +100 at the exit and -1 per step.
- Solved with **value iteration** on the Bellman optimality equation
  `V(s) = max_a Σ_s' P(s' | s, a) [R(s') + γ V(s')]`, with `γ = 0.95` and convergence threshold `θ = 1e-6`. The optimal policy is shown as arrows on the grid and can be simulated step by step.

## Results

Measured with [`scripts/evaluate.py`](scripts/evaluate.py) (seeds 0–999, no rendering):

| Agent | Setup | Outcome |
|---|---|---|
| Bayesian greedy agent (Part 2) | 1,000 random palaces, max 200 turns | **50.1 %** mission completed, 8.5 % died, 41.4 % stuck (turn limit reached) |
| Value-iteration policy (Part 3) | 1,000 random rivers x 100 episodes | **99.5 %** reached the exit, mean return 82.4, mean 18.1 steps |

The MDP policy is optimal for the model by construction. All of its failures (470 episodes, concentrated in 37 of the 1,000 rivers) hit the 200-step limit; none ended in a wrong terminal state. The Bayesian agent rarely dies, since the risk threshold works, but it often gets stuck: a one-step greedy policy oscillates between low-risk cells when no safe unexplored cell is adjacent. A planning step over the belief state (for example, expected-risk shortest paths) would be the natural next improvement.

## How to run

Requires Python 3.10+.

```bash
pip install -r requirements.txt

# Part 1: search / logical inference (choose MANUAL or AUTO)
cd Parte_1 && python kurtz.py

# Part 2: Bayesian agent (choose ascii or heatmap view)
cd Parte_2 && python palacio.py

# Part 3: river MDP with value iteration
cd Parte_2 && python river_mdp.py

# Reproduce the results table
python scripts/evaluate.py --n 1000
```

The interactive modes clear the screen with `cls`, so they are meant for a Windows terminal.

## Stack

Python (standard library: `dataclasses`, `collections`, `random`), Matplotlib for the belief heatmaps.
