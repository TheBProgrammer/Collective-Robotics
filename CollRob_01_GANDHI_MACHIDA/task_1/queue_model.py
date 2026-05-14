import math
import random


def poisson_pmf(i, alpha):
    lam = alpha # delta_t=1
    return (math.exp(-lam) * (lam ** i)) / math.factorial(i)

def sample_poisson(alpha):
    u = random.random()
    cumulative = 0.0
    i = 0
    while True:
        cumulative += poisson_pmf(i, alpha)
        if u < cumulative:
            return i
        i += 1

def simulate_queue(alpha, processing_duration, n_steps=2000):
    queue_length = 0
    total_queue = 0
    processing_remaining = 0

    for _ in range(n_steps):
        # New jobs arrive
        new_jobs = sample_poisson(alpha)
        queue_length += new_jobs

        # Process current job (one at a time)
        if processing_remaining > 0:
            processing_remaining -= 1
        elif queue_length > 0:
            queue_length -= 1
            processing_remaining = processing_duration - 1

        total_queue += queue_length

    return total_queue / n_steps # Average queue length over all steps
