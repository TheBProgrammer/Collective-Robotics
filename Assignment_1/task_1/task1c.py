"""Task 1c: Simulate 2000 steps with alpha=0.1, processing duration=4. Report avg queue length."""
from queue_model import simulate_queue

alpha = 0.1
processing_duration = 4
n_steps = 2000

avg_queue = simulate_queue(alpha, processing_duration, n_steps)
print(f"Simulation: alpha={alpha}, processing_duration={processing_duration}, steps={n_steps}")
print(f"Average queue length: {avg_queue:.4f}")
