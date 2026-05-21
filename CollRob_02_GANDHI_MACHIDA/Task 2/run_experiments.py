#!/usr/bin/env python3
"""
Runs ARGoS headless for each swarm size in SWARM_SIZES, captures
the DATA log lines emitted by each robot, and saves one CSV file
per run plus a combined all_runs.csv.
"""

import subprocess
import re
import csv
import sys
import time
from pathlib import Path

# Configuration
SWARM_SIZES = [5, 10, 20, 30, 50]    # robots per run
EXPERIMENT_DURATION = 300            # simulated seconds per run
ARGOS_CONFIG = "task2.argos"         # template config
DATA_DIR = Path("data")              # output directory
CLUSTER_THRESHOLD   = 0.99           # fraction of robots stopped


def patch_config(template: str, n_robots: int, duration: int) -> str:
    """Patch robot quantity and experiment duration into the argos template"""
    cfg = re.sub(r'quantity="\d+"', f'quantity="{n_robots}"', template)
    cfg = re.sub(r'length="\d+"',   f'length="{duration}"',   cfg)
    return cfg


def parse_output(output: str, n_robots: int) -> list[dict]:
    """Extract DATA lines from combined stdout+stderr"""

    rows = []
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("DATA,"):
            continue
        parts = line.split(",")
        if len(parts) != 5:
            continue
        _, robot_id, tick, neighbor_count, stopped = parts
        try:
            rows.append({
                "tick"          : int(tick),
                "robot_id"      : robot_id,
                "neighbor_count": int(neighbor_count),
                "stopped"       : int(stopped),
                "swarm_size"    : n_robots,
            })
        except ValueError:
            continue   # skip malformed lines
    return rows


def run_single(n_robots: int, template: str) -> list[dict]:
    """ Patch config, run argos3 headlessly, write LOG to a file, parse DATA rows """
    print(f"\nRunning N = {n_robots} robots  ({EXPERIMENT_DURATION}s sim)", flush=True)
    t0 = time.perf_counter()

    patched    = patch_config(template, n_robots, EXPERIMENT_DURATION)
    tmp_config = DATA_DIR / f"_tmp_N{n_robots}.argos"
    log_file   = DATA_DIR / f"_log_N{n_robots}.txt"
    tmp_config.write_text(patched)

    try:
        subprocess.run(
            # -z  : no Qt window (headless)
            # -l  : write LOG stream to file
            ["argos3", "-z", "-l", str(log_file), "-c", str(tmp_config)],
            capture_output=True,
            text=True,
            timeout=900,
        )
        log_text = log_file.read_text() if log_file.exists() else ""

    except subprocess.TimeoutExpired:
        print(f" Timeout for N={n_robots}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print(" 'argos3' not found in PATH. Is ARGoS installed?", file=sys.stderr)
        sys.exit(1)
    finally:
        tmp_config.unlink(missing_ok=True)
        if log_file.exists():
            log_file.unlink()

    elapsed = time.perf_counter() - t0
    rows = parse_output(log_text, n_robots)

    # Check clusters
    if rows:
        ticks = sorted({r["tick"] for r in rows})
        for tick in ticks:
            tick_rows = [r for r in rows if r["tick"] == tick]
            fraction  = sum(r["stopped"] for r in tick_rows) / len(tick_rows)
            if fraction >= CLUSTER_THRESHOLD:
                print(f" -> Cluster formed at tick {tick} "
                      f"({tick / 10:.1f}s sim, {fraction*100:.0f}% stopped)")
                break
            else:
                max_tick = max(r["tick"] for r in rows)
                tick_rows = [r for r in rows if r["tick"] == max_tick]
                fraction  = sum(r["stopped"] for r in tick_rows) / len(tick_rows)
                print(f" -> No full cluster in {EXPERIMENT_DURATION}s "
                    f"(final stopped fraction: {fraction*100:.0f}%)")

    print(f"   -> {len(rows):,} data rows  |  wall time: {elapsed:.1f}s", flush=True)
    return rows

def save_csv(rows: list[dict], filepath: Path) -> None:
    """Write rows to a CSV file"""
    if not rows:
        print(f"No data to write for {filepath.name}", file=sys.stderr)
        return
    fieldnames = ["tick", "robot_id", "neighbor_count", "stopped", "swarm_size"]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows):,} rows {filepath}")

def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    config_path = Path(ARGOS_CONFIG)
    if not config_path.exists():
        print(f"Config file '{ARGOS_CONFIG}' not found.\n"
              f"   Run this script from the ass_2/ directory.", file=sys.stderr)
        sys.exit(1)

    template = config_path.read_text()

    print("=" * 56)
    print("  Task 2.4 – Swarm Size Analysis")
    print(f"  Sizes   : {SWARM_SIZES}")
    print(f"  Duration: {EXPERIMENT_DURATION} s/run")
    print(f"  Output  : {DATA_DIR}/")
    print("=" * 56)

    all_rows: list[dict] = []

    for n in SWARM_SIZES:
        rows = run_single(n, template)
        all_rows.extend(rows)
        save_csv(rows, DATA_DIR / f"swarm_N{n}.csv")

    # Combined dataset
    save_csv(all_rows, DATA_DIR / "all_runs.csv")

    print("\n" + "=" * 56)
    print(f"  All {len(SWARM_SIZES)} runs complete!")
    print(f"     Total rows: {len(all_rows):,}")
    print(f"     Next step : python3 plot_results.py")
    print("=" * 56 + "\n")

if __name__ == "__main__":
    main()
