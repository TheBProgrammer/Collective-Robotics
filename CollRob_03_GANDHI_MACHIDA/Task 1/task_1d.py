# Buffon's Needle Simulation - Task 1d
# Task 1d: Visualize the convergence of the estimated probability 
# to the true probability as n increases, and include confidence intervals.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# constants
L = 0.7     # length of needle
D = 1.0     # distance between the lines
max_n = 100
num_experiments = 50

# arrays
x = np.random.uniform(0, D/2, size=(num_experiments, max_n))
theta = np.random.uniform(0, np.pi/2, size=(num_experiments, max_n))
intersections = x <= (L / 2) * np.sin(theta)

# running probabilities
running_crossings = np.cumsum(intersections, axis=1)
n_array = np.arange(1, max_n + 1)
running_P = running_crossings / n_array

# 95% confidence intervals
mean_P = np.mean(running_P, axis=0)
margin_of_error = 1.96 * np.sqrt((1/n_array) * mean_P * (1 - mean_P))
ci_upper = mean_P + margin_of_error
ci_lower = mean_P - margin_of_error

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_facecolor('black')
ax.grid(color='yellow', linestyle='--', alpha=0.3)

# Plot all 50 experiments as thin lines
for i in range(num_experiments):
    ax.plot(n_array, running_P[i], color='cyan', alpha=0.2, linewidth=1.2)

# Plot the 95% confidence interval bounds
ax.plot(n_array, ci_upper, color='red', linestyle='--', linewidth=2)
ax.plot(n_array, ci_lower, color='red', linestyle='--', linewidth=2)

# Plot the true probability for reference
true_P = (2 * L) / (D * np.pi)
ax.axhline(y=true_P, color='white', linestyle='-', linewidth=2)

ax.set_title(f"Running Estimated Probability over n Trials ({num_experiments} experiments)")
ax.set_xlabel("Number of Trials (n)")
ax.set_ylabel("Estimated Probability of Crossing")
ax.set_ylim(0.1, 0.8) # Zoom in to see the funnel effect

# Custom clean legend
custom_lines = [Line2D([0], [0], color='cyan', alpha=0.5, lw=2),
                Line2D([0], [0], color='red', linestyle='--', lw=2),
                Line2D([0], [0], color='white', linestyle='-', lw=2)]
ax.legend(custom_lines, ['Experiment Runs', '95% Confidence Interval', 'True Probability'], 
          facecolor='white', framealpha=0.9, loc='upper right')

plt.tight_layout()
plt.savefig("CollRob_03_GANDHI_MACHIDA/Task 1/plots/1d_probability_convergence.png")
plt.show()