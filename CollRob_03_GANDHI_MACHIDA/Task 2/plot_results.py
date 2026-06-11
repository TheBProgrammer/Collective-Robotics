#!/usr/bin/env python3
"""
Tutorial 3 - Task 2: Plot the effect of anti-agents on swarm aggregation.

Reads data/all_runs.csv (or per-run CSVs) and generates:
    1. plots/task2_stopped_over_time.png  - stopped fraction vs sim time, per pct
    2. plots/task2_biggest_cluster.png    - biggest spatial cluster vs anti-pct
    3. plots/task2_time_to_cluster.png    - mean time to reach 80% stopped vs pct
    4. plots/task2_leave_orders.png       - leave orders issued per anti-agent vs pct

Spatial clustering: two normal robots are in the same cluster if their
Euclidean distance is below CLUSTER_DIST (meters). The biggest cluster
size is the largest connected-component size after union-find.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR  = Path("data")
PLOTS_DIR = Path("plots")
TICKS_PER_SECOND = 10
CLUSTER_DIST     = 0.35       # m - link two robots if closer than this
STOPPED_THRESH   = 0.80       # fraction of normal robots stopped -> "clustered"
LAST_WINDOW_S    = 20         # seconds at the end of the run used for stats

PALETTE = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#9b5de5"]


def load() -> pd.DataFrame:
    f = DATA_DIR / "all_runs.csv"
    if not f.exists():
        print(f"Missing {f}. Run run_experiments.py first.", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(f)
    print(f"loaded {len(df):,} rows from {f}")
    return df


def union_find_max(points: np.ndarray, threshold: float) -> int:
    """Return the size of the largest connected component induced by the
    distance graph (edge if dist < threshold)."""
    n = len(points)
    if n == 0:
        return 0
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    diffs = points[:, None, :] - points[None, :, :]
    d2 = np.sum(diffs * diffs, axis=-1)
    t2 = threshold * threshold
    pairs = np.argwhere((d2 < t2) & (d2 > 0))
    for i, j in pairs:
        if i < j:
            union(int(i), int(j))

    roots = [find(i) for i in range(n)]
    _, counts = np.unique(roots, return_counts=True)
    return int(counts.max())


def stopped_fraction(df: pd.DataFrame) -> pd.DataFrame:
    """Per (pct, rep, tick): fraction of normal robots in STOPPED state."""
    normals = df[df["role"] == "N"]
    grp = (normals.groupby(["anti_pct", "rep", "tick"])
                  .agg(stopped_frac=("metric_f", "mean"))
                  .reset_index())
    return grp


def biggest_cluster_per_tick(df: pd.DataFrame) -> pd.DataFrame:
    """Per (pct, rep, tick): biggest spatial cluster among STOPPED normals."""
    normals = df[(df["role"] == "N") & (df["metric_f"] == 1)]
    out = []
    for (pct, rep, tick), grp in normals.groupby(["anti_pct", "rep", "tick"]):
        pts = grp[["x", "y"]].to_numpy()
        out.append({"anti_pct": pct, "rep": rep, "tick": tick,
                    "biggest_cluster": union_find_max(pts, CLUSTER_DIST)})
    return pd.DataFrame(out)


def time_to_cluster(stop_df: pd.DataFrame) -> pd.DataFrame:
    """First tick where stopped fraction reaches STOPPED_THRESH (per run)."""
    out = []
    for (pct, rep), grp in stop_df.groupby(["anti_pct", "rep"]):
        hit = grp[grp["stopped_frac"] >= STOPPED_THRESH]
        ttc = int(hit["tick"].min()) if not hit.empty else None
        out.append({"anti_pct": pct, "rep": rep, "ttc_ticks": ttc})
    return pd.DataFrame(out)


def style_ax(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, alpha=0.25, linestyle="--")


def plot_stopped_over_time(stop_df: pd.DataFrame, percentages, out_path):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for color, pct in zip(PALETTE, percentages):
        d = stop_df[stop_df["anti_pct"] == pct]
        mean = d.groupby("tick")["stopped_frac"].mean()
        std  = d.groupby("tick")["stopped_frac"].std()
        t = mean.index.to_numpy() / TICKS_PER_SECOND
        ax.plot(t, mean.values, label=f"{pct}%  anti-agents", color=color, linewidth=2)
        ax.fill_between(t, (mean - std).values, (mean + std).values,
                        color=color, alpha=0.15)
    ax.axhline(STOPPED_THRESH, color="red", linestyle="--", linewidth=1,
               label=f"{int(STOPPED_THRESH*100)}% threshold")
    ax.set_ylim(-0.02, 1.05)
    style_ax(ax, "Aggregation kinetics vs anti-agent percentage",
             "Simulation time (s)", "Fraction of normal robots STOPPED")
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")


def plot_biggest_cluster(cluster_df: pd.DataFrame, out_path):
    """Average biggest-cluster size in the final window vs anti percentage."""
    max_tick    = cluster_df["tick"].max()
    cutoff      = max_tick - LAST_WINDOW_S * TICKS_PER_SECOND
    final       = cluster_df[cluster_df["tick"] >= cutoff]

    agg = (final.groupby(["anti_pct", "rep"])["biggest_cluster"].mean()
                .reset_index())
    summary = (agg.groupby("anti_pct")["biggest_cluster"]
                  .agg(["mean", "std", "count"]).reset_index())

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.errorbar(summary["anti_pct"], summary["mean"], yerr=summary["std"],
                fmt="-o", color="#264653", capsize=4, linewidth=2,
                markersize=8, label="mean ± std")
    # Annotate values
    for _, row in summary.iterrows():
        ax.annotate(f"{row['mean']:.1f}",
                    (row["anti_pct"], row["mean"]),
                    textcoords="offset points", xytext=(8, 6),
                    fontsize=9, fontweight="bold")
    style_ax(ax, "Biggest cluster size vs anti-agent percentage",
             "Anti-agent percentage (%)", "Biggest cluster (# robots)")
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")
    return summary


def plot_time_to_cluster(ttc_df: pd.DataFrame, out_path):
    """Mean time-to-cluster vs anti percentage, with std error bars."""
    ttc_df = ttc_df.copy()
    ttc_df["ttc_s"] = ttc_df["ttc_ticks"] / TICKS_PER_SECOND
    summary = (ttc_df.groupby("anti_pct")["ttc_s"]
                     .agg(["mean", "std", "count"]).reset_index())
    failures = (ttc_df.assign(failed=ttc_df["ttc_ticks"].isna())
                      .groupby("anti_pct")["failed"].mean()
                      .reset_index().rename(columns={"failed": "fail_frac"}))

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.errorbar(summary["anti_pct"], summary["mean"], yerr=summary["std"],
                fmt="-s", color="#e76f51", capsize=4, linewidth=2,
                markersize=8, label=f"time to reach {int(STOPPED_THRESH*100)}%")
    for _, row in summary.iterrows():
        if not np.isnan(row["mean"]):
            ax.annotate(f"{row['mean']:.0f}s",
                        (row["anti_pct"], row["mean"]),
                        textcoords="offset points", xytext=(8, 6),
                        fontsize=9, fontweight="bold")
    style_ax(ax, "Time to reach aggregation threshold",
             "Anti-agent percentage (%)", "Time to cluster (s)")
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")
    return summary, failures


def plot_leave_orders(df: pd.DataFrame, out_path):
    """Mean leave orders issued per anti-agent over the whole run, per pct."""
    anti = df[df["role"] == "A"]
    if anti.empty:
        return
    # Each row is one log entry per tick per anti-agent; metric_f == 1 means
    # the anti-agent broadcast a leave order at that tick.
    per_run = (anti.groupby(["anti_pct", "rep"])["metric_f"].sum() /
               anti.groupby(["anti_pct", "rep"])["robot_id"].nunique())
    per_run = per_run.reset_index().rename(columns={0: "orders_per_agent"})
    per_run.columns = ["anti_pct", "rep", "orders_per_agent"]
    summary = (per_run.groupby("anti_pct")["orders_per_agent"]
                       .agg(["mean", "std"]).reset_index())

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.bar(summary["anti_pct"].astype(str), summary["mean"],
           yerr=summary["std"], color=PALETTE[:len(summary)],
           edgecolor="white", capsize=4)
    max_y = (summary["mean"] + summary["std"].fillna(0)).max()
    for i, row in summary.iterrows():
        bar_top = row["mean"] + (row["std"] if not np.isnan(row["std"]) else 0)
        ax.text(i, bar_top + max_y * 0.02,
                f"{row['mean']:.1f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold")
    ax.set_ylim(0, max_y * 1.20)
    style_ax(ax, "Leave-orders issued per anti-agent",
             "Anti-agent percentage (%)", "Leave orders per anti-agent (logged)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")


def main():
    PLOTS_DIR.mkdir(exist_ok=True)
    df = load()
    percentages = sorted(df["anti_pct"].unique())

    print("computing per-tick stopped fractions...")
    stop_df = stopped_fraction(df)

    print("computing biggest-cluster sizes...")
    cluster_df = biggest_cluster_per_tick(df)

    print("computing time-to-cluster...")
    ttc_df = time_to_cluster(stop_df)

    print("\ngenerating plots:")
    plot_stopped_over_time(stop_df, percentages,
                           PLOTS_DIR / "task2_stopped_over_time.png")
    bc_summary = plot_biggest_cluster(cluster_df,
                                      PLOTS_DIR / "task2_biggest_cluster.png")
    ttc_summary, failures = plot_time_to_cluster(ttc_df,
                                  PLOTS_DIR / "task2_time_to_cluster.png")
    plot_leave_orders(df, PLOTS_DIR / "task2_leave_orders.png")

    print("\nSummary - biggest cluster (final window):")
    print(bc_summary.to_string(index=False))
    print("\nSummary - time to cluster (s):")
    print(ttc_summary.to_string(index=False))
    print("\nFailure fraction per pct:")
    print(failures.to_string(index=False))

    # Save numerical summaries for the report.
    bc_summary.to_csv(DATA_DIR / "summary_biggest_cluster.csv", index=False)
    ttc_summary.to_csv(DATA_DIR / "summary_time_to_cluster.csv", index=False)
    failures.to_csv(DATA_DIR / "summary_failures.csv", index=False)


if __name__ == "__main__":
    main()
