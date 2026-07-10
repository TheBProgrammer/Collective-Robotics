"""
Tutorial 5 - Task 2: Density-dependent global switching.

The swarm converges to a majority of left- or right-goers, but occasionally
switches to the other majority. In real locusts this happens more often at low
density. We test whether the simulation reproduces that.

For a swarm size N we define three zones on the left-goer count L:

    Zone A: L > 0.7 N
    Zone B: 0.3 N <= L <= 0.7 N
    Zone C: L < 0.3 N

A global switch is a crossing A -> C or C -> A. While the swarm sits in A or C
the counter is zero; on entering B it starts counting. Leaving B into the
opposite zone stores the counter (that is one switch time); leaving B back into
the zone it came from resets the counter without storing.

We report two quantities:

  * crossing time  -- the counter defined above, i.e. the number of time steps
    the swarm spends inside zone B during a successful crossing;
  * waiting time   -- the number of time steps between two consecutive
    switches, which is what "time between global switches" means in the
    biological literature and which is the quantity that carries the
    density dependence.

All swarm sizes are simulated for the same number of time steps, so the
"number of observed switches" is directly comparable across N.

Usage:  python task_2.py
"""

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import os
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from locust import simulate  # noqa: E402

# Task 1 parameter set; only N varies here.
C = 0.5
SPEED = 0.01
R = 0.045
SWITCH_PROB = 0.15

SWARM_SIZES = [20, 30, 40, 50, 65, 80, 95, 110, 130, 150]
RUNS_PER_SIZE = 10
TIME_STEPS = 200_000        # per run; >> the 5,000 required by the sheet


def zone_of(L, N):
    """'A' if L > 0.7N, 'C' if L < 0.3N, else 'B'."""
    if L > 0.7 * N:
        return "A"
    if L < 0.3 * N:
        return "C"
    return "B"


def switch_times(L, N):
    """Crossing durations of the zone-B traversals that connect A to C.

    Returns a list of counter values, one per observed global switch. A run
    that begins inside zone B is not counted until it has first touched A or C,
    because until then there is no zone of origin to compare against.
    """
    times = []
    origin = None   # zone the current B-crossing started from
    counter = 0

    for L_t in L:
        z = zone_of(L_t, N)

        if z in ("A", "C"):
            if origin is not None and origin != z:
                # Left B into the opposite extreme: a global switch.
                times.append(counter)
            # Entering (or staying in) an extreme zone always resets.
            origin = z
            counter = 0
        else:
            # In zone B: count only once an origin zone is known.
            if origin is not None:
                counter += 1

    return times


def switch_steps(L, N):
    """Time-step indices at which each global switch completes."""
    steps = []
    origin = None
    for t, L_t in enumerate(L):
        z = zone_of(L_t, N)
        if z in ("A", "C"):
            if origin is not None and origin != z:
                steps.append(t)
            origin = z
    return steps


def _one_run(args):
    """Worker: simulate once, return (crossing_times, switch_step_indices)."""
    N, seed, T = args
    L = simulate(N=N, T=T, C=C, speed=SPEED, r=R, p=SWITCH_PROB, seed=seed)
    return switch_times(L, N), switch_steps(L, N)


def collect(swarm_sizes=SWARM_SIZES, runs=RUNS_PER_SIZE, T=TIME_STEPS):
    """Sweep swarm sizes in parallel; return per-size statistics."""
    jobs = [(N, 1000 * N + rep, T) for N in swarm_sizes for rep in range(runs)]

    workers = min(os.cpu_count() or 1, 8)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_one_run, jobs))
    print(f"  {len(jobs)} runs on {workers} workers in "
          f"{time.perf_counter() - t0:.0f}s\n")

    stats = {"N": [], "mean_cross": [], "std_cross": [],
             "mean_wait": [], "std_wait": [], "count": []}

    for i, N in enumerate(swarm_sizes):
        block = results[i * runs:(i + 1) * runs]

        crossings = [c for times, _ in block for c in times]
        # Waiting times are the gaps between consecutive switches, measured
        # within each run (never across the run boundary).
        waits = [b - a for _, steps in block for a, b in zip(steps, steps[1:])]

        stats["N"].append(N)
        stats["count"].append(len(crossings))
        stats["mean_cross"].append(np.mean(crossings) if crossings else np.nan)
        stats["std_cross"].append(np.std(crossings) if crossings else np.nan)
        stats["mean_wait"].append(np.mean(waits) if waits else np.nan)
        stats["std_wait"].append(np.std(waits) if waits else np.nan)

        print(f"  N={N:>3}  switches={len(crossings):>6}  "
              f"crossing={stats['mean_cross'][-1]:8.2f}  "
              f"waiting={stats['mean_wait'][-1]:12.1f}", flush=True)

    return {k: np.array(v, dtype=float) for k, v in stats.items()}


def plot(s):
    plot_dir = Path(__file__).resolve().parent / "plots"
    plot_dir.mkdir(exist_ok=True)
    N = s["N"]
    total_steps = RUNS_PER_SIZE * TIME_STEPS

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))

    axes[0].errorbar(N, s["mean_cross"], yerr=s["std_cross"], marker="o",
                     capsize=4, color="steelblue")
    axes[0].set_xlabel("Swarm size $N$")
    axes[0].set_ylabel("Mean crossing time (time steps)")
    axes[0].set_title("Time spent in zone B per switch")
    axes[0].grid(alpha=0.3)

    axes[1].errorbar(N, s["mean_wait"], yerr=s["std_wait"], marker="o",
                     capsize=4, color="darkgreen")
    axes[1].set_xlabel("Swarm size $N$")
    axes[1].set_ylabel("Mean waiting time (time steps)")
    axes[1].set_title("Time between consecutive global switches")
    axes[1].set_yscale("log")
    axes[1].grid(alpha=0.3, which="both")

    axes[2].plot(N, s["count"], marker="s", color="firebrick")
    axes[2].set_xlabel("Swarm size $N$")
    axes[2].set_ylabel("Observed switches")
    axes[2].set_title(f"Switches in {total_steps:,} time steps per size")
    axes[2].set_yscale("symlog", linthresh=1)
    axes[2].grid(alpha=0.3, which="both")

    fig.tight_layout()
    out = plot_dir / "task_2_switching.png"
    fig.savefig(out, dpi=150)
    print(f"\nSaved {out}")


def main():
    print(f"Task 2: {len(SWARM_SIZES)} swarm sizes x {RUNS_PER_SIZE} runs "
          f"x {TIME_STEPS:,} steps")
    stats = collect()
    plot(stats)
    np.savez(Path(__file__).resolve().parent / "task_2_results.npz", **stats)


if __name__ == "__main__":
    main()
