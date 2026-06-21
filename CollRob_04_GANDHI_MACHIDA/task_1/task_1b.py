from task_1a import simulate
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.pylab import seed

# params
N           = 20        # number of locusts
T           = 500       # time steps

def build_transition_histogram(num_runs=1000):
    A = np.zeros((N+1, N+1), dtype=int)
    
    for run in range(num_runs):
        left_counts = simulate(T)
        for t in range(T):
            Lt   = left_counts[t]
            Lt1  = left_counts[t+1]
            A[Lt, Lt1] += 1
    
    return A

def plot_histogram(A):
    plot_dir = Path(__file__).resolve().parent / "plots"
    plot_dir.mkdir(exist_ok=True)

    plt.figure(figsize=(7, 6))
    plt.imshow(A, origin='lower', cmap='hot')
    plt.colorbar(label="Frequency")
    plt.xlabel("L_{t+1} (next state)")
    plt.ylabel("L_t (current state)")
    plt.title("Task 1b - Transition histogram (1000 runs x 500 steps)")
    plt.tight_layout()
    plt.savefig(plot_dir / "task_1b.png", dpi=150)
    plt.show()

if __name__ == "__main__":
    print("Running 1000 simulations...")
    A = build_transition_histogram(num_runs=1000)
    plot_histogram(A)
