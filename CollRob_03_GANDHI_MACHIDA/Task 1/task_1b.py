# Buffon's Needle Simulation
# Task 1b: Simulate the dropping of needles and estimate the probability of crossing and the value of pi.

import numpy as np
import matplotlib.pyplot as plt

# Constants
L = 0.7     # length of needle  
D = 1       # distance between the lines
n = 1000    # number of drops

# array for distance and angles
x = np.random.uniform(0, D/2, n)            # distance from the center of the needle to the nearest line
theta = np.random.uniform(0, np.pi/2, n)    # angle of the needle with respect to the lines

# Apply the mathematical condition
intersections = x <= (L / 2) * np.sin(theta)
total_crossings = np.sum(intersections)

# probability
estimated_probability = total_crossings / n

# estimations
# Theoretical probability for comparison
true_probability = (2 * L) / (D * np.pi)

# Estimate pi using the formula derived in 1a: pi ≈ (2 * L * n) / (D * total_crossings)
estimated_pi = (2 * L * n) / (D * max(total_crossings, 1))

print(f"Estimated Probability: {estimated_probability:.4f} (True: {true_probability:.4f})")
print(f"Estimated Pi:          {estimated_pi:.4f} (True: {np.pi:.4f})")

# Output:
# Estimated Probability: 0.4520 (True: 0.4456)
# Estimated Pi:          3.0973 (True: 3.1416)

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_facecolor('black')

# Draw 6 parallel lines (from y=0 to y=5)
num_lines = 6
for i in range(num_lines):
    ax.axhline(y=i * D, color='yellow', linestyle='--', alpha=1.0, linewidth=1.5)

# Map the mathematical 'x' (distance to nearest line) to actual Y-coordinates
line_assignments = np.random.randint(1, num_lines - 1, n)
above_or_below = np.random.choice([1, -1], n)
y_centers = (line_assignments * D) + (above_or_below * x)

# Generate random X-coordinates
x_centers = np.random.uniform(0, 10, n)

# Randomly mirror the angle so the needles point in all directions visually
plot_theta = theta * np.random.choice([1, -1], n)

# Calculate the end points of the needles for plotting
dx = (L / 2) * np.cos(plot_theta)
dy = (L / 2) * np.sin(plot_theta)

x1 = x_centers - dx
x2 = x_centers + dx
y1 = y_centers - dy
y2 = y_centers + dy

# Separate the coordinates based on the boolean 'intersections' array you created
cross_x1, cross_x2 = x1[intersections], x2[intersections]
cross_y1, cross_y2 = y1[intersections], y2[intersections]

miss_x1, miss_x2 = x1[~intersections], x2[~intersections]
miss_y1, miss_y2 = y1[~intersections], y2[~intersections]

# Plot intersecting needles in red, missing needles in blue
ax.plot([cross_x1, cross_x2], [cross_y1, cross_y2], color='red', alpha=0.6, linewidth=1.5)
ax.plot([miss_x1, miss_x2], [miss_y1, miss_y2], color='blue', alpha=0.6, linewidth=1.5)

# legend
ax.plot([], [], color='red', label='Crossing')
ax.plot([], [], color='blue', label='Missing')
ax.plot([], [], color='yellow', linestyle='--', label='Grid Lines')
ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), facecolor='white', framealpha=0.9)

ax.set_aspect('equal')
ax.set_title(f"Buffon's Needle Simulation (n={n})\nEstimated pi approx {estimated_pi:.4f}")
ax.set_xlim(0, 10)
ax.set_ylim(0, (num_lines - 1) * D)
plt.tight_layout()
plt.savefig("CollRob_03_GANDHI_MACHIDA/Task 1/plots/1b_buffon_needle_simulation.png")

