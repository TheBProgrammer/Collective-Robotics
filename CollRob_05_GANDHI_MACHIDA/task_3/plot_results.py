#!/usr/bin/env python3
"""
Tutorial 5 - Task 3: plots for the foraging sweep.

Reads data/summary.csv and data/all_runs.csv (produced by run_experiments.py)
and writes the figures to plots/.

Can be run on the host (numpy/pandas/matplotlib) or inside the container.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
PLOT_DIR = Path(__file__).resolve().parent / "plots"


def load():
    summary = pd.read_csv(DATA_DIR / "summary.csv")
    runs = pd.read_csv(DATA_DIR / "all_runs.csv")
    return summary, runs


def power_law_exponent(N, mean):
    """Fit collected ~ c * N**alpha. alpha < 1 means sublinear scaling."""
    alpha, log_c = np.polyfit(np.log(N), np.log(mean), 1)
    return alpha, np.exp(log_c)


def plot_performance(summary):
    """Swarm performance and per-robot performance over swarm size."""
    g = summary.groupby("n_robots")["collected"]
    N = g.mean().index.values
    mean, std = g.mean().values, g.std().values
    per = summary.assign(pr=summary.collected / summary.n_robots)
    per_mean = per.groupby("n_robots")["pr"]

    # The single-robot rate is a poor anchor for an "ideal linear" reference:
    # it is small, noisy, and a lone robot has no team-mate to stumble upon an
    # object it missed. Fit the scaling instead, and also fit it over N >= 2.
    a_all, c_all = power_law_exponent(N, mean)
    a_2up, c_2up = power_law_exponent(N[1:], mean[1:])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))

    ax1.errorbar(N, mean, yerr=std, marker="o", capsize=4, color="steelblue",
                 label="measured", zorder=3)
    grid = np.linspace(N[0], N[-1], 100)
    ax1.plot(grid, c_2up * grid ** a_2up, "-", color="firebrick", lw=1.4,
             label=rf"fit $N \geq 2$: $\propto N^{{{a_2up:.2f}}}$")
    ax1.plot(grid, mean[1] / 2 * grid, "--", color="gray",
             label="linear in $N$ (anchored at $N=2$)")
    ax1.set_xlabel("Swarm size $N$")
    ax1.set_ylabel("Objects collected in 300 s")
    ax1.set_title("Swarm performance over swarm size")
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.3)

    ax2.errorbar(N, per_mean.mean().values, yerr=per_mean.std().values,
                 marker="s", capsize=4, color="firebrick")
    ax2.set_xlabel("Swarm size $N$")
    ax2.set_ylabel("Objects collected per robot")
    ax2.set_title("Per-robot performance (interference)")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    out = PLOT_DIR / "task_3_performance.png"
    fig.savefig(out, dpi=150)
    print(f"  {out}")
    print(f"    scaling exponent: alpha = {a_all:.2f} (all N), "
          f"{a_2up:.2f} (N >= 2)")


def plot_behaviour(runs):
    """Where the interference comes from: collisions and time budget."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))

    coll = runs.groupby("n_robots")["collision"].mean() * 100
    bound = runs.groupby("n_robots")["boundary"].mean() * 100
    ax1.plot(coll.index, coll.values, marker="o", color="firebrick",
             label="collision (robot-robot)")
    ax1.plot(bound.index, bound.values, marker="s", color="steelblue",
             label="arena boundary")
    ax1.set_xlabel("Swarm size $N$")
    ax1.set_ylabel("% of control cycles")
    ax1.set_title("Contact events over swarm size")
    ax1.legend()
    ax1.grid(alpha=0.3)

    states = ["SEARCH", "APPROACH", "TRANSPORT", "BACKUP", "TURN"]
    frac = (runs.groupby(["n_robots", "state"]).size()
                .unstack(fill_value=0))
    frac = frac.reindex(columns=states, fill_value=0)
    frac = frac.div(frac.sum(axis=1), axis=0) * 100

    bottom = np.zeros(len(frac))
    for s in states:
        ax2.bar(frac.index, frac[s].values, bottom=bottom, label=s)
        bottom += frac[s].values
    ax2.set_xlabel("Swarm size $N$")
    ax2.set_ylabel("% of control cycles")
    ax2.set_title("Time budget of the controller")
    ax2.legend(fontsize=8, loc="lower right")
    ax2.set_ylim(0, 100)

    fig.tight_layout()
    out = PLOT_DIR / "task_3_behaviour.png"
    fig.savefig(out, dpi=150)
    print(f"  {out}")


def plot_estimate_vs_truth(summary):
    """The robots' own delivery count vs the simulator's ground truth."""
    fig, ax = plt.subplots(figsize=(5.6, 5.0))
    ax.scatter(summary.collected, summary.estimated, alpha=0.55,
               c=summary.n_robots, cmap="viridis")
    lim = [0, max(summary.collected.max(), summary.estimated.max()) + 2]
    ax.plot(lim, lim, "--", color="gray", label="perfect agreement")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Objects collected (ground truth)")
    ax.set_ylabel("Deliveries reported by the robots")
    ax.set_title("Camera-based estimate vs ground truth")
    cbar = fig.colorbar(ax.collections[0], ax=ax)
    cbar.set_label("Swarm size $N$")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.tight_layout()
    out = PLOT_DIR / "task_3_estimate_vs_truth.png"
    fig.savefig(out, dpi=150)
    print(f"  {out}")


def summarize(summary, runs):
    print("\n  N   collected        per-robot     collisions   transporting")
    for n, grp in summary.groupby("n_robots"):
        r = runs[runs.n_robots == n]
        print(f"  {n:>2}  {grp.collected.mean():5.1f} +- {grp.collected.std():4.1f}"
              f"   {grp.collected.mean()/n:6.2f}"
              f"        {100*r.collision.mean():5.1f}%"
              f"        {100*r.transporting.mean():5.1f}%")

    bias = summary.estimated.sum() / summary.collected.sum()
    print(f"\n  robots over-report deliveries by {100*(bias-1):.0f}% overall")


def main():
    PLOT_DIR.mkdir(exist_ok=True)
    summary, runs = load()
    print("Writing plots:")
    plot_performance(summary)
    plot_behaviour(runs)
    plot_estimate_vs_truth(summary)
    summarize(summary, runs)


if __name__ == "__main__":
    main()
