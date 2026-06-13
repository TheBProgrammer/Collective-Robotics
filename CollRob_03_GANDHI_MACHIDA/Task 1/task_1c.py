# Buffon's Needle Simulation - Standard Deviation Analysis
# Task 1c: Analyze how the standard deviation of the estimated probability changes 
# with the number of trials (n) in the simulation.

import numpy as np
import matplotlib.pyplot as plt

# Constants
L = 0.7     # length of needle
D = 1       # distance between the lines
num_experiments = 1000    

n_values = np.arange(10, 1010, 10)      # range of n values
std_devs = []                           # to store standard deviations for each n   

print("Running simulations...")
for n in n_values:
    # generate 2D matrices (10,000 exps, n drops each)
    x = np.random.uniform(0, D/2, size=(num_experiments, n))
    theta = np.random.uniform(0, np.pi/2, size=(num_experiments, n))

    # intersection condition
    intersections = x <= (L / 2) * np.sin(theta)
    crossing_per_exp = np.sum(intersections, axis=1)

    # crossings to probability
    probabilities = crossing_per_exp / n

    # store std deviation for this n
    current_std = np.std(probabilities)
    std_devs.append(current_std)

print("Simulations completed. Plotting results...")

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_facecolor('black')
ax.grid(color='yellow', linestyle='--', alpha=0.3)

# Plot the standard deviation curve
ax.plot(n_values, std_devs, color='cyan', linewidth=2, label='Standard Deviation')

ax.set_title("Standard Deviation of Intersection Probability over $n$ Trials\n(10,000 experiments per $n$)")
ax.set_xlabel("Number of Trials ($n$)")
ax.set_ylabel("Standard Deviation")
ax.tick_params(colors='black')
ax.legend(facecolor='white', framealpha=0.9)

plt.tight_layout()
plt.savefig("CollRob_03_GANDHI_MACHIDA/Task 1/plots/1c_std_dev_vs_n.png")
plt.show()