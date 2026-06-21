import numpy as np
from pathlib import Path
from task_1a import simulate
import matplotlib.pyplot as plt
from matplotlib.pylab import seed
from task_1b import build_transition_histogram

# params
N           = 20        # number of locusts
T           = 500       # time steps

# Normalize histogram -> transition probabilities
def compute_transition_probs(A):
    M = np.sum(A, axis=1, keepdims=True)        # row sums, shape (21, 1)
    P = np.where(M > 0, A / M, 0)              # normalize, avoid div by zero
    return P

# Sample one trajectory using P
def sample_trajectory(P, T, L0=None):
    L0 = L0 if L0 is not None else np.random.randint(0, N+1)
    trajectory = [L0]
    for _ in range(T):
        L_t    = trajectory[-1]
        L_next = np.random.choice(N+1, p=P[L_t])
        trajectory.append(L_next)
    return trajectory

# Plot: sampled trajectory vs real simulation
def plot_task1c(P):
    plot_dir = Path(__file__).resolve().parent / "plots"
    plot_dir.mkdir(exist_ok=True)
 
    traj_sampled = sample_trajectory(P, T)
    traj_real    = simulate(T, seed=42)
 
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
 
    axes[0].plot(traj_real, color='steelblue')
    axes[0].set_ylabel("Left-goers L")
    axes[0].set_title("Task 1a - Real simulation (full swarm)")
    axes[0].set_ylim(0, N)
 
    axes[1].plot(traj_sampled, color='darkorange')
    axes[1].set_ylabel("Left-goers L")
    axes[1].set_title("Task 1c - Sampled trajectory (from transition probabilities)")
    axes[1].set_ylim(0, N)
    axes[1].set_xlabel("Time step")
 
    plt.tight_layout()
    plt.savefig(plot_dir / "task_1c.png", dpi=150)
    plt.show()

if __name__ == "__main__":
    print("Building transition histogram (1000 runs)...")
    A = build_transition_histogram(num_runs=1000)
 
    print("Computing transition probabilities...")
    P = compute_transition_probs(A)
 
    print("Sampling trajectory and plotting...")
    plot_task1c(P)
