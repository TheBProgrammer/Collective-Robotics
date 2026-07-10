"""
Shared locust simulation for Tutorial 5 (tasks 1 and 2).

Continuous-space, discrete-time locusts on a ring of circumference C.
Each locust moves left (-1) or right (+1) at constant speed and flips
direction in one of two situations:

  1) the majority of locusts within its perception range r move opposite to it,
  2) spontaneously, with probability p per time step.

This is the same model as Tutorial 4 task 1, but parameterized (Tutorial 5
uses C = 0.5, speed = 0.01, N = 50, p = 0.15) and vectorized: the per-locust
Python loop is replaced by a pairwise-distance matrix, which matters because
task 1 needs 5000 runs and task 2 needs runs of 5000+ steps.
"""

import numpy as np

# Tutorial 5 parameter set (task 1; task 2 varies N).
C = 0.5
SPEED = 0.01
R = 0.045
SWITCH_PROB = 0.15
N = 50


def init_swarm(n, C=C, rng=None):
    """Uniform random positions on the ring, random directions in {-1, +1}."""
    rng = np.random.default_rng() if rng is None else rng
    positions = rng.uniform(0.0, C, n)
    directions = rng.choice(np.array([-1, 1]), n)
    return positions, directions


def step(positions, directions, C=C, speed=SPEED, r=R, p=SWITCH_PROB, rng=None):
    """Advance the swarm by one time step. Returns (positions, directions)."""
    rng = np.random.default_rng() if rng is None else rng

    pos32 = positions.astype(np.float32)
    delta = np.abs(pos32[:, None] - pos32[None, :])
    arc = np.minimum(delta, np.float32(C) - delta)

    mask = (arc < np.float32(r)).astype(np.float32)
    net_dir = mask @ directions.astype(np.float32) - directions

    # Rule 1: flip when the neighbour majority moves the other way
    majority_dir = np.sign(net_dir)
    flip_majority = (majority_dir != 0) & (majority_dir != directions)

    # Rule 2: spontaneous flip, applied on top of rule 1
    flip_spontaneous = rng.random(len(positions)) < p

    new_directions = directions * np.where(flip_majority, -1, 1)
    new_directions = new_directions * np.where(flip_spontaneous, -1, 1)

    new_positions = (positions + speed * new_directions) % C
    return new_positions, new_directions


def simulate(N=N, T=500, C=C, speed=SPEED, r=R, p=SWITCH_PROB, seed=None):
    """Run one simulation. Returns the left-goer counts L_t, length T + 1."""
    rng = np.random.default_rng(seed)
    positions, directions = init_swarm(N, C=C, rng=rng)

    left_counts = np.empty(T + 1, dtype=np.int32)
    left_counts[0] = np.count_nonzero(directions == -1)

    for t in range(1, T + 1):
        positions, directions = step(
            positions, directions, C=C, speed=speed, r=r, p=p, rng=rng
        )
        left_counts[t] = np.count_nonzero(directions == -1)

    return left_counts
