import matplotlib.pyplot as plt
from collections import Counter
from queue_model import poisson_pmf, sample_poisson

N_SAMPLES = 10000
alpha = 0.5

samples = [sample_poisson(alpha) for _ in range(N_SAMPLES)]
counts = Counter(samples)
max_i = max(counts.keys())

xs = list(range(max_i + 1))
empirical = [counts.get(i, 0) / N_SAMPLES for i in xs]
theoretical = [poisson_pmf(i, alpha) for i in xs]

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(xs, empirical, alpha=0.6, label=f"Empirical ({N_SAMPLES} samples)", color="steelblue")
ax.plot(xs, theoretical, "ro-", label="Theoretical P(X=i)", linewidth=2, markersize=6)
ax.set_xlabel("i (number of jobs)")
ax.set_ylabel("Probability")
ax.set_title(f"Sampling from Poisson PMF (α = {alpha})")
ax.legend()
plt.tight_layout()
plt.savefig("task1b_sampling.png", dpi=150)
print("Saved task1b_sampling.png")
plt.show()
