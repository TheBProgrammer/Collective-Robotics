import matplotlib.pyplot as plt
from queue_model import simulate_queue

N_RUNS = 200
N_STEPS = 2000
PROCESSING_DURATION = 4
ALPHA_START = 0.005
ALPHA_END = 0.25
ALPHA_STEP = 0.005

alphas = []
a = ALPHA_START
while a <= ALPHA_END + 1e-9:
    alphas.append(round(a, 4))
    a += ALPHA_STEP

avg_queue_lengths = []
for alpha in alphas:
    run_avgs = [simulate_queue(alpha, PROCESSING_DURATION, N_STEPS) for _ in range(N_RUNS)]
    avg_queue_lengths.append(sum(run_avgs) / N_RUNS)
    print(f"alpha={alpha:.3f}  avg_queue={avg_queue_lengths[-1]:.4f}")

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(alphas, avg_queue_lengths, "b-o", markersize=4, linewidth=1.5)
ax.set_xlabel("Arrival rate α")
ax.set_ylabel("Average queue length")
ax.set_title(
    f"Average queue length vs α\n"
    f"(processing duration = {PROCESSING_DURATION} steps, {N_RUNS} runs × {N_STEPS} steps)"
)
ax.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("task1d_avg_queue_4steps.png", dpi=150)
print("Saved task1d_avg_queue_4steps.png")
plt.show()
