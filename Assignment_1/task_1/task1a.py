"""Task 1a: Plot P(X=i) for alpha in {0.01, 0.1, 0.5, 1} over a reasonable range of X."""
import matplotlib.pyplot as plt
from queue_model import poisson_pmf

alphas = [0.01, 0.1, 0.5, 1]
colors = ["steelblue", "darkorange", "green", "red"]

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.flatten()

for ax, alpha, color in zip(axes, alphas, colors):
    # reasonable range: go up to where P(X=i) becomes negligible
    max_i = max(10, int(alpha * 5 + 10))
    xs = list(range(max_i + 1))
    probs = [poisson_pmf(i, alpha) for i in xs]

    ax.bar(xs, probs, color=color, alpha=0.8, edgecolor="black", linewidth=0.5)
    ax.set_title(f"α = {alpha}", fontsize=12)
    ax.set_xlabel("i (number of jobs)")
    ax.set_ylabel("P(X = i)")
    ax.set_xlim(-0.5, max_i + 0.5)

fig.suptitle("Poisson PMF for different arrival rates α (λ = α, Δt = 1)", fontsize=13)
plt.tight_layout()
plt.savefig("task1a_poisson_pmf.png", dpi=150)
print("Saved task1a_poisson_pmf.png")
plt.show()
