from matplotlib.pylab import seed
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# params
N           = 20        # number of locusts
C           = 1.0       # ring circumference
SPEED       = 0.001     # speed of locusts
R           = 0.045     # perception range
SWITCH_PROB = 0.015     # spontaneous switch probability
T           = 500       # time steps

# initialize positions and directions
def init_swarm(n):
    positions  = np.random.uniform(0, 1, n)         # random positions on the ring
    directions = np.random.choice([-1, 1], n)       # random initial directions (-1 or +1)
    return positions, directions

# simulate one time step
def step(positions, directions):
    n = len(positions)
    new_directions = directions.copy()
 
    for i in range(n):
        # shortest arc distance from locust i to all others
        distances     = np.abs(positions - positions[i])
        arc_distances = np.minimum(distances, 1 - distances)
 
        # neighbors within range r, excluding self
        mask          = np.arange(n) != i
        neighbor_dirs = directions[(arc_distances < R) & mask]
 
        # Rule 1: majority opposite -> flip
        if len(neighbor_dirs) > 0:
            majority_dir = np.sign(np.sum(neighbor_dirs))
            if majority_dir != directions[i] and majority_dir != 0:
                new_directions[i] *= -1
 
        # Rule 2: spontaneous switch with probability P
        if np.random.rand() < SWITCH_PROB:
            new_directions[i] *= -1
 
    # update positions with wrap-around
    positions = (positions + SPEED * new_directions) % C
 
    return positions, new_directions

def simulate(T, seed=None):
    if seed is not None:
        np.random.seed(seed)

    positions, directions = init_swarm(N)
    left_counts = [np.sum(directions == -1)]
 
    for _ in range(T):
        positions, directions = step(positions, directions)
        left_counts.append(np.sum(directions == -1))
 
    return left_counts

# Task 1a: single run plot
def task_1a():
    left_counts = simulate(T)
 
    plot_dir = Path(__file__).resolve().parent / "plots"
    plot_dir.mkdir(exist_ok=True)

    plt.figure(figsize=(10, 4))
    plt.plot(left_counts, color='steelblue')
    plt.xlabel("Time step")
    plt.ylabel("Number of left-going locusts")
    plt.title("Task 1a - Left-goers over time (single run, N=20)")
    plt.ylim(0, N)
    plt.tight_layout()
    plt.savefig(plot_dir / "task_1a.png", dpi=150)
    plt.show()

if __name__ == "__main__":
    task_1a()
