#!/usr/bin/env python3
"""
Reads the CSV files produced by run_experiments.py and generates
three separate plots saved to plots/.

Plots:
  1. Stopped fraction over time   – one line per swarm size
  2. Time-to-cluster vs N         – bar chart (ticks until 99% stopped)
  3. Cluster stability            – box plot of neighbour count in final 30 ticks

Cluster definition: first tick where ≥ 99% of robots are in STOPPED state.
"""

import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Config
DATA_DIR = Path("data")
PLOTS_DIR = Path("plots")
CLUSTER_THRESHOLD  = 0.99     # 99 % of robots stopped → clustered
FINAL_WINDOW_TICKS = 30       # last N ticks used for stability analysis
TICKS_PER_SECOND   = 10       # from the .argos file (for axis labels)

# Colour palette
PALETTE = ["#4361ee", "#3a0ca3", "#7209b7", "#f72585", "#fb8500"]

def load_data() -> pd.DataFrame:
    csv_files = sorted(DATA_DIR.glob("swarm_N*.csv"))
    if not csv_files:
        print(f"No CSV files found in '{DATA_DIR}/'.\n"
              f"   Run python3 run_experiments.py first.", file=sys.stderr)
        sys.exit(1)

    frames = []
    for f in csv_files:
        df = pd.read_csv(f)
        frames.append(df)
        print(f"  Loaded {f.name}: {len(df):,} rows")
    return pd.concat(frames, ignore_index=True)

def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Per (swarm_size, tick): mean stopped fraction and mean neighbour count."""
    return (
        df.groupby(["swarm_size", "tick"])
        .agg(
            stopped_fraction =("stopped",        "mean"),
            avg_neighbors    =("neighbor_count",  "mean"),
            robot_count      =("robot_id",        "nunique"),
        )
        .reset_index()
        .sort_values(["swarm_size", "tick"])
    )

def time_to_cluster(agg: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """
    For each swarm_size: first tick where stopped_fraction >= threshold.
    Returns None for runs that never reached the threshold.
    """
    records = []
    for n, grp in agg.groupby("swarm_size"):
        hit = grp[grp["stopped_fraction"] >= threshold]
        ttc = int(hit["tick"].min()) if not hit.empty else None
        records.append({"swarm_size": int(n), "ttc_ticks": ttc})
    return pd.DataFrame(records)

def style_ax(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.tick_params(labelsize=10)

def plot_stopped_over_time(ax, agg: pd.DataFrame, swarm_sizes, colors):
    """Plot 1: stopped fraction vs tick for each N."""
    for color, n in zip(colors, swarm_sizes):
        data = agg[agg["swarm_size"] == n].sort_values("tick")
        # Smooth with a rolling mean for readability
        smoothed = data["stopped_fraction"].rolling(window=3, min_periods=1).mean()
        ax.plot(
            (data["tick"] / TICKS_PER_SECOND).to_numpy(),
            smoothed.to_numpy(),
            label=f"N = {n}",
            color=color,
            linewidth=2.2,
        )

    ax.axhline(
        y=CLUSTER_THRESHOLD,
        color="#e63946",
        linestyle="--",
        linewidth=1.4,
        label=f"{CLUSTER_THRESHOLD*100:.0f}% threshold",
    )
    ax.set_ylim(-0.02, 1.08)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))

    style_ax(ax,
             "Cluster Formation Over Time",
             "Simulation Time (s)",
             "Robots in STOPPED State")
    ax.legend(fontsize=9, framealpha=0.8)

def plot_time_to_cluster(ax, ttc_df: pd.DataFrame, colors):
    """Plot 2: time-to-cluster (s) vs swarm size."""
    labels  = [f"N={int(r.swarm_size)}" for _, r in ttc_df.iterrows()]
    values  = [
        r.ttc_ticks / TICKS_PER_SECOND if pd.notna(r.ttc_ticks) else None
        for _, r in ttc_df.iterrows()
    ]
    valid_values = [v for v in values if v is not None]
    label_offset = max(valid_values) * 0.015 if valid_values else 1

    bars = ax.bar(
        labels,
        [v if v is not None else 0 for v in values],
        color=colors[:len(labels)],
        edgecolor="white",
        linewidth=1.2,
        width=0.6,
    )

    for bar, val in zip(bars, values):
        if val is None:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                3,
                "N/A",
                ha="center", va="bottom",
                fontsize=9, color="#888",
            )
        else:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + label_offset,
                f"{val:.0f}s",
                ha="center", va="bottom",
                fontsize=9, fontweight="bold",
            )

    style_ax(ax,
             "Time to Form Cluster vs Swarm Size",
             "Swarm Size",
             "Time to Cluster (s, 99% stopped)")


def plot_stability(ax, df: pd.DataFrame, swarm_sizes, colors):
    """Plot 3: distribution of neighbour count in the final FINAL_WINDOW_TICKS."""
    max_tick     = df["tick"].max()
    cutoff_tick  = max_tick - FINAL_WINDOW_TICKS
    final_df     = df[df["tick"] >= cutoff_tick]

    data_by_n = [
        final_df[final_df["swarm_size"] == n]["neighbor_count"].values
        for n in swarm_sizes
    ]

    bp = ax.boxplot(
        data_by_n,
        labels=[f"N={n}" for n in swarm_sizes],
        patch_artist=True,
        medianprops=dict(color="white", linewidth=2),
        whiskerprops=dict(linewidth=1.4),
        capprops=dict(linewidth=1.4),
        flierprops=dict(marker="o", markersize=3, alpha=0.4),
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.78)

    style_ax(ax,
             f"Cluster Stability (Final {FINAL_WINDOW_TICKS} Ticks)",
             "Swarm Size",
             "Neighbour Count per Robot")


def save_single_plot(filename: str, plot_func, *args) -> None:
    """Create one standalone figure, run a plotting function on it, and save it."""
    fig, ax = plt.subplots(figsize=(8, 5.5), facecolor="#f8f9fa")
    ax.set_facecolor("#f8f9fa")

    plot_func(ax, *args)

    plt.tight_layout(pad=2.0)
    out = PLOTS_DIR / filename
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f" Plot saved -> {out}")


def main() -> None:
    PLOTS_DIR.mkdir(exist_ok=True)

    print("=" * 56)
    print(" Plotting Swarm Aggregation Results")
    print("=" * 56)

    df  = load_data()
    agg = aggregate(df)

    swarm_sizes = sorted(df["swarm_size"].unique())
    colors      = PALETTE[:len(swarm_sizes)]

    ttc_df = time_to_cluster(agg, CLUSTER_THRESHOLD)
    print("\n  Time-to-cluster summary:")
    for _, row in ttc_df.iterrows():
        ttc_s = (
            f"{row['ttc_ticks'] / TICKS_PER_SECOND:.1f}s"
            if pd.notna(row["ttc_ticks"])
            else "N/A"
        )
        print(f"    N={int(row['swarm_size']):<4} → {ttc_s}")

    print("\n  Saving plots:")
    save_single_plot(
        "task2_stopped_over_time.png",
        plot_stopped_over_time,
        agg,
        swarm_sizes,
        colors,
    )
    save_single_plot(
        "task2_time_to_cluster.png",
        plot_time_to_cluster,
        ttc_df,
        colors,
    )
    save_single_plot(
        "task2_cluster_stability.png",
        plot_stability,
        df,
        swarm_sizes,
        colors,
    )

    plt.show()

if __name__ == "__main__":
    main()
