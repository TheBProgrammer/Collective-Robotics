#!/usr/bin/env python3
"""
Tutorial 5 - Task 3: foraging sweep over swarm size.

Runs the ARGoS foraging experiment for swarm sizes N = 1..10, several
independent repetitions each, and records:

  * the number of objects collected (ground truth, from the loop functions),
  * the per-tick controller outputs of every robot (the six values required by
    the task sheet).

Must be executed inside the ARGoS container, e.g.

    ./run_docker.sh experiments

Output:
    data/summary.csv    one row per (N, repetition): collected objects etc.
    data/all_runs.csv   per-tick controller outputs, all runs concatenated
"""

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import csv
import os
import re
import subprocess
import sys
import time

SWARM_SIZES = list(range(1, 11))
REPETITIONS = 20
DURATION = 300            # simulated seconds per run
ARGOS_CONFIG = "task3.argos"
DATA_DIR = Path("data")

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def patch_config(template: str, n_robots: int, duration: int, seed: int) -> str:
    """Set robot count, length and seed; strip visualization to run headless."""
    cfg = re.sub(r'(<entity quantity=")\d+("[^>]*>\s*<foot-bot id="fb")',
                 rf'\g<1>{n_robots}\g<2>', template)
    cfg = re.sub(r'length="\d+"', f'length="{duration}"', cfg)
    cfg = re.sub(r'random_seed="\d+"', f'random_seed="{seed}"', cfg)
    cfg = re.sub(r'<visualization>.*?</visualization>', '', cfg, flags=re.DOTALL)
    return cfg


def parse_log(text: str, n_robots: int, rep: int):
    """Return (collected, rows) from one run's log."""
    collected = None
    rows = []
    for line in text.splitlines():
        line = ANSI.sub("", line).strip()

        if line.startswith("COLLECTED,"):
            collected = int(line.split(",")[1])

        elif line.startswith("DATA,"):
            p = line.split(",")
            if len(p) != 15:
                continue
            try:
                rows.append({
                    "n_robots": n_robots, "rep": rep,
                    "robot_id": p[1], "tick": int(p[2]),
                    "vl": float(p[3]), "vr": float(p[4]),
                    "error": int(p[5]), "collision": int(p[6]),
                    "boundary": int(p[7]), "transporting": int(p[8]),
                    "home": int(p[9]), "force": int(p[10]),
                    "delivered": int(p[11]), "state": p[12],
                    "x": float(p[13]), "y": float(p[14]),
                })
            except ValueError:
                continue

    return collected, rows


def run_single(args):
    n_robots, rep, template = args
    seed = 2000 + 37 * n_robots + rep
    tmp_cfg = DATA_DIR / f"_tmp_n{n_robots}_r{rep}.argos"
    log_file = DATA_DIR / f"_log_n{n_robots}_r{rep}.txt"
    tmp_cfg.write_text(patch_config(template, n_robots, DURATION, seed))

    t0 = time.perf_counter()
    try:
        subprocess.run(["argos3", "-l", str(log_file), "-c", str(tmp_cfg)],
                       capture_output=True, text=True, timeout=900)
        text = log_file.read_text() if log_file.exists() else ""
    except subprocess.TimeoutExpired:
        print(f"     timeout N={n_robots} rep={rep}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("     'argos3' not found -- run inside the container "
              "(./run_docker.sh experiments)", file=sys.stderr)
        sys.exit(1)
    finally:
        tmp_cfg.unlink(missing_ok=True)
        log_file.unlink(missing_ok=True)

    collected, rows = parse_log(text, n_robots, rep)
    if collected is None:
        print(f"     no COLLECTED line for N={n_robots} rep={rep}", file=sys.stderr)
        return None

    # Robot-side estimate, for comparison with the ground truth.
    estimated = sum(1 for line in text.splitlines()
                    if ANSI.sub("", line).startswith("DELIVER,"))

    elapsed = time.perf_counter() - t0
    print(f"  N={n_robots:>2} rep={rep:>2}  collected={collected:>3}  "
          f"estimated={estimated:>3}  ({elapsed:4.1f}s)", flush=True)

    return {
        "n_robots": n_robots, "rep": rep, "seed": seed,
        "collected": collected, "estimated": estimated,
        "per_robot": collected / n_robots,
    }, rows


def save_csv(rows, path, fieldnames):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path}  ({len(rows):,} rows)")


def main():
    DATA_DIR.mkdir(exist_ok=True)
    cfg = Path(ARGOS_CONFIG)
    if not cfg.exists():
        sys.exit(f"config '{ARGOS_CONFIG}' not found")
    template = cfg.read_text()

    jobs = [(n, r, template) for n in SWARM_SIZES for r in range(REPETITIONS)]
    workers = min(os.cpu_count() or 1, 8)

    print("=" * 66)
    print("  Tutorial 5 - Task 3: foraging, swarm size sweep")
    print(f"  swarm sizes  : {SWARM_SIZES}")
    print(f"  repetitions  : {REPETITIONS}")
    print(f"  duration/run : {DURATION} s      workers: {workers}")
    print("=" * 66)

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = [r for r in pool.map(run_single, jobs) if r is not None]

    summary = [s for s, _ in results]
    all_rows = [row for _, rows in results for row in rows]

    print("=" * 66)
    save_csv(summary, DATA_DIR / "summary.csv",
             ["n_robots", "rep", "seed", "collected", "estimated", "per_robot"])
    save_csv(all_rows, DATA_DIR / "all_runs.csv",
             ["n_robots", "rep", "robot_id", "tick", "vl", "vr", "error",
              "collision", "boundary", "transporting", "home", "force",
              "delivered", "state", "x", "y"])
    print(f"  finished {len(summary)} runs in {time.perf_counter() - t0:.0f}s")
    print("  next: python3 plot_results.py")
    print("=" * 66)


if __name__ == "__main__":
    main()
