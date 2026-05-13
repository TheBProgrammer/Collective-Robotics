import math
import random


def poisson_pmf(i, alpha):
    """P(X=i) for Poisson with lambda=alpha (delta_t=1)."""
    lam = alpha
    return (math.exp(-lam) * (lam ** i)) / math.factorial(i)


def sample_poisson(alpha):
    """Sample number of incoming jobs from Poisson(alpha) using numpy-free inversion."""
    lam = alpha
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        p *= random.random()
        k += 1
    return k - 1


def simulate_queue(alpha, processing_duration, n_steps=2000):
    """
    Simulate the computer queue for n_steps time steps.
    Each step: sample new jobs (add to queue), then process one job if queue non-empty.
    Returns the average queue length over all steps.
    """
    queue_length = 0
    total_queue = 0
    processing_remaining = 0

    for _ in range(n_steps):
        # Phase 1: new jobs arrive
        new_jobs = sample_poisson(alpha)
        queue_length += new_jobs

        # Phase 2: process current job (one at a time)
        if processing_remaining > 0:
            processing_remaining -= 1
        elif queue_length > 0:
            queue_length -= 1
            processing_remaining = processing_duration - 1

        total_queue += queue_length

    return total_queue / n_steps
