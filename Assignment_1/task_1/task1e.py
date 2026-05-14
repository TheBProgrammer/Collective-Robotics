import matplotlib.pyplot as plt
from queue_model import simulate_queue

N_RUNS = 200
N_STEPS = 2000

# --- 4-step configuration (reproduce 1d data for comparison) ---
PROC_4 = 4
alphas_4 = [round(0.005 * k, 4) for k in range(1, 51)]   # 0.005 to 0.25

# --- 2-step configuration ---
PROC_2 = 2
alphas_2 = [round(0.005 * k, 4) for k in range(1, 101)]  # 0.005 to 0.5


def run_experiment(alphas, proc_duration):
    results = []
    for alpha in alphas:
        run_avgs = [simulate_queue(alpha, proc_duration, N_STEPS) for _ in range(N_RUNS)]
        mean = sum(run_avgs) / N_RUNS
        results.append(mean)
        print(f"  proc={proc_duration}  alpha={alpha:.3f}  avg_queue={mean:.4f}")
    return results


print("Running 4-step experiment...")
avg_4 = run_experiment(alphas_4, PROC_4)

print("Running 2-step experiment...")
avg_2 = run_experiment(alphas_2, PROC_2)

fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)

axes[0].plot(alphas_4, avg_4, "b-o", markersize=3, linewidth=1.5)
axes[0].set_xlabel("Arrival rate α")
axes[0].set_ylabel("Average queue length")
axes[0].set_title(f"Processing duration = {PROC_4} steps\nα ∈ [0.005, 0.25]")
axes[0].grid(True, linestyle="--", alpha=0.5)

axes[1].plot(alphas_2, avg_2, "r-o", markersize=3, linewidth=1.5)
axes[1].set_xlabel("Arrival rate α")
axes[1].set_ylabel("Average queue length")
axes[1].set_title(f"Processing duration = {PROC_2} steps\nα ∈ [0.005, 0.5]")
axes[1].grid(True, linestyle="--", alpha=0.5)

fig.suptitle(
    f"Average queue length vs α  ({N_RUNS} runs × {N_STEPS} steps each)",
    fontsize=13
)
plt.tight_layout()
plt.savefig("task1e_comparison.png", dpi=150)
print("Saved task1e_comparison.png")
plt.show()
