#!/usr/bin/env python3
"""
Tutorial 3 - Task 2: Anti-agents in swarm aggregation.

Sweeps the percentage of anti-agents in a swarm of fixed total size and runs
several repetitions for each configuration. For every run we parse the DATA
lines emitted by both Lua controllers (normal robots and anti-agents) and
save the rows to CSV.

Output layout:
    data/
        runs_pct<P>_rep<R>.csv     -- one file per (percent, repetition)
        all_runs.csv               -- concatenated dataset
"""

import csv
import re
import subprocess
import sys
import time
from pathlib import Path

# Configuration
TOTAL_ROBOTS         = 30                          # total swarm size (normals + anti-agents)
ANTI_PERCENTAGES     = [0, 5, 10, 15, 20, 30]      # % of anti-agents to test
REPETITIONS          = 5                           # independent runs per setting
EXPERIMENT_DURATION  = 200                         # simulated seconds per run
ARGOS_CONFIG         = "task2.argos"
DATA_DIR             = Path("data")


def patch_config(template: str, n_normal: int, n_anti: int,
                 duration: int, seed: int) -> str:
    """Patch normal/anti quantities, length, seed, and strip visualization."""
    cfg = re.sub(r'(<entity quantity=")\d+("[^>]*>\s*<foot-bot id="nb")',
                 rf'\g<1>{n_normal}\g<2>', template)
    cfg = re.sub(r'(<entity quantity=")\d+("[^>]*>\s*<foot-bot id="aa")',
                 rf'\g<1>{n_anti}\g<2>', template)
    cfg = re.sub(r'length="\d+"',      f'length="{duration}"',   cfg)
    cfg = re.sub(r'random_seed="\d+"', f'random_seed="{seed}"',  cfg)
    # Strip the qt-opengl block so we can run headless (this ARGoS build
    # has no -z flag).
    cfg = re.sub(r'<visualization>.*?</visualization>', '', cfg,
                 flags=re.DOTALL)
    # If we ended up with no <entity quantity="..."> for one of the roles
    # (n=0), distribute blocks for that role become invalid; drop them.
    if n_anti == 0:
        cfg = re.sub(r'<distribute>(?:(?!</distribute>).)*?<foot-bot id="aa".*?</distribute>',
                     '', cfg, flags=re.DOTALL)
    if n_normal == 0:
        cfg = re.sub(r'<distribute>(?:(?!</distribute>).)*?<foot-bot id="nb".*?</distribute>',
                     '', cfg, flags=re.DOTALL)
    return cfg


def parse_output(text: str, pct: int, rep: int,
                 n_normal: int, n_anti: int) -> list[dict]:
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("DATA,"):
            continue
        parts = line.split(",")
        if len(parts) != 8:
            continue
        _, role, robot_id, tick, x, y, c, flag = parts
        try:
            rows.append({
                "anti_pct"   : pct,
                "rep"        : rep,
                "n_normal"   : n_normal,
                "n_anti"     : n_anti,
                "role"       : role,          # N or A
                "robot_id"   : robot_id,
                "tick"       : int(tick),
                "x"          : float(x),
                "y"          : float(y),
                "metric_c"   : int(c),        # neighbours (N) / stopped_near (A)
                "metric_f"   : int(flag),     # stopped (N) / issued_leave (A)
            })
        except ValueError:
            continue
    return rows


def run_single(pct: int, rep: int, template: str) -> list[dict]:
    n_anti   = round(TOTAL_ROBOTS * pct / 100)
    n_normal = TOTAL_ROBOTS - n_anti
    seed     = 1000 + pct * 31 + rep

    print(f"  pct={pct:>2}% rep={rep}  (N={n_normal}, A={n_anti}, seed={seed})",
          flush=True)
    t0 = time.perf_counter()

    patched   = patch_config(template, n_normal, n_anti,
                             EXPERIMENT_DURATION, seed)
    tmp_cfg   = DATA_DIR / f"_tmp_p{pct}_r{rep}.argos"
    log_file  = DATA_DIR / f"_log_p{pct}_r{rep}.txt"
    tmp_cfg.write_text(patched)

    try:
        subprocess.run(
            ["argos3", "-l", str(log_file), "-c", str(tmp_cfg)],
            capture_output=True, text=True, timeout=900,
        )
        log_text = log_file.read_text() if log_file.exists() else ""
    except subprocess.TimeoutExpired:
        print(f"     Timeout for pct={pct} rep={rep}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("     'argos3' not found. Are you running inside the container?",
              file=sys.stderr)
        sys.exit(1)
    finally:
        tmp_cfg.unlink(missing_ok=True)
        if log_file.exists():
            log_file.unlink()

    elapsed = time.perf_counter() - t0
    rows = parse_output(log_text, pct, rep, n_normal, n_anti)
    print(f"     {len(rows):>6,} rows | {elapsed:5.1f}s wall", flush=True)
    return rows


def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        print(f"  no rows for {path.name}", file=sys.stderr)
        return
    fieldnames = ["anti_pct", "rep", "n_normal", "n_anti",
                  "role", "robot_id", "tick", "x", "y",
                  "metric_c", "metric_f"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    cfg_path = Path(ARGOS_CONFIG)
    if not cfg_path.exists():
        print(f"Config '{ARGOS_CONFIG}' not found", file=sys.stderr)
        sys.exit(1)

    template = cfg_path.read_text()

    print("=" * 64)
    print("  Tutorial 3 - Task 2: Anti-agent sweep")
    print(f"  total robots       : {TOTAL_ROBOTS}")
    print(f"  anti percentages   : {ANTI_PERCENTAGES}")
    print(f"  repetitions / pct  : {REPETITIONS}")
    print(f"  duration / run     : {EXPERIMENT_DURATION} s")
    print("=" * 64)

    all_rows: list[dict] = []
    for pct in ANTI_PERCENTAGES:
        for rep in range(REPETITIONS):
            rows = run_single(pct, rep, template)
            all_rows.extend(rows)
            save_csv(rows, DATA_DIR / f"runs_pct{pct:02d}_rep{rep}.csv")

    save_csv(all_rows, DATA_DIR / "all_runs.csv")

    print("=" * 64)
    print(f"  finished. total rows: {len(all_rows):,}")
    print(f"  next: python3 plot_results.py")
    print("=" * 64)


if __name__ == "__main__":
    main()
