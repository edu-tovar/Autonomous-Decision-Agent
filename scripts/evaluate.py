"""Headless evaluation of the Part 2 agents over many random seeds.

Runs the Bayesian greedy agent (palacio.main) and the value-iteration policy
for the river MDP without rendering, and prints the outcome statistics
reported in the README.
"""
import argparse
import os
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("agg")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Parte_2"))

import palacio  # noqa: E402
import palacio_world  # noqa: E402
import river_mdp  # noqa: E402


class TurnLimit(Exception):
    pass


def run_bayesian_agent(seed: int, max_turns: int) -> str:
    """Play one palace and return 'win', 'death' or 'timeout'."""
    log = []
    turns = {"n": 0}

    def capture(*args, **kwargs):
        log.append(" ".join(map(str, args)))

    def count_turn(_seconds):
        # palacio.main sleeps once per turn: use it as the turn counter.
        turns["n"] += 1
        if turns["n"] > max_turns:
            raise TurnLimit

    palacio.print = capture
    palacio_world.print = capture
    palacio.time.sleep = count_turn
    palacio.os.system = lambda *_: 0

    try:
        palacio.main(seed=seed, reveal=False, modo="ascii")
    except TurnLimit:
        return "timeout"
    text = "\n".join(log)
    if "VICTORIA" in text:
        return "win"
    if "MUERTE" in text:
        return "death"
    return "other"


def evaluate_bayesian(n: int, max_turns: int) -> None:
    results = [run_bayesian_agent(seed, max_turns) for seed in range(n)]
    print(f"Bayesian greedy agent: {n} palaces, max {max_turns} turns")
    for outcome in ("win", "death", "timeout", "other"):
        count = results.count(outcome)
        print(f"  {outcome:8s} {count:5d}  ({100 * count / n:.1f} %)")


def evaluate_river(n: int, episodes: int) -> None:
    success, returns, steps = [], [], []
    for world_seed in range(n):
        rio = river_mdp.RiverWorld(filas=7, cols=6, nislas=2, seed=world_seed)
        rio.reset()
        _, pi = river_mdp.value_iteration(rio, gamma=0.95, theta=1e-6)
        for episode_seed in range(episodes):
            ok, total, path = river_mdp.simulate_episode(rio, pi, seed=episode_seed, render=False)
            success.append(ok)
            returns.append(total)
            steps.append(len(path) - 1)
    print(f"River MDP (value iteration): {n} rivers x {episodes} episodes")
    print(f"  success rate {100 * sum(success) / len(success):.1f} %")
    print(f"  mean return  {statistics.mean(returns):.1f}")
    print(f"  mean steps   {statistics.mean(steps):.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000, help="number of random worlds")
    parser.add_argument("--episodes", type=int, default=100, help="episodes per river")
    parser.add_argument("--max-turns", type=int, default=200)
    args = parser.parse_args()
    evaluate_bayesian(args.n, args.max_turns)
    evaluate_river(args.n, args.episodes)
