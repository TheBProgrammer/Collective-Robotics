# Buffon's Needle Simulation - Task 1e
# Task 1e: Evaluate the accuracy of the confidence intervals by 
# checking how many of the estimated probabilities fall outside the 
# 95% confidence intervals as n increases.

import numpy as np
import matplotlib.pyplot as plt

# Constants
L = 0.7     # length of needle
D = 1       # distance between the lines
max_n = 100
num_experiments = 10000

# arrays
x = np.random.uniform(0, D/2, size=(num_experiments, max_n))
theta = np.random.uniform(0, np.pi/2, size=(num_experiments, max_n))
intersections = x <= (L / 2) * np.sin(theta)

# running probabilities
running_crossings = np.cumsum(intersections, axis=1)
n_array = np.arange(1, max_n + 1)
running_P = running_crossings / n_array

# True probability
true_P = (2 * L) / (D * np.pi)

# unique confidence interval for each exp
margins = 1.96 * np.sqrt((1/n_array) * running_P * (1 - running_P))
upper_bounds = running_P + margins
lower_bounds = running_P - margins

# true probability outside confidence intervals
outside_bounds = (true_P < lower_bounds) | (true_P > upper_bounds)

# ratio of exps outside bounds
outsid_counts = np.sum(outside_bounds, axis=0)
outside_ratio = outsid_counts / num_experiments

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_facecolor('black')
ax.grid(color='yellow', linestyle='--', alpha=0.3)

# Plot the ratio curve
ax.plot(n_array, outside_ratio, color='cyan', linewidth=2, label='Measured Ratio Outside CI')

# Plot the expected 5% line (since it's a 95% confidence interval)
ax.axhline(y=0.05, color='red', linestyle='--', linewidth=2, label='Expected Ratio (0.05)')

ax.set_title("Ratio of Experiments Outside 95% Confidence Interval")
ax.set_xlabel("Number of Trials ($n$)")
ax.set_ylabel("Ratio Outside CI")
ax.tick_params(colors='black') 
ax.legend(facecolor='white', framealpha=0.9)

plt.tight_layout()
plt.savefig("CollRob_03_GANDHI_MACHIDA/Task 1/plots/1e_ratio_outside_ci.png")
plt.show()
