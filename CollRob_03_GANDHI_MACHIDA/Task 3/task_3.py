import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist

# simulation params
n_values = np.arange(2, 202, 2)
r_values = [0.05, 0.1, 0.25, 0.5]
num_experiments = 1000

# store results
mean_estimates_error = {r: [] for r in r_values}
std_estimates = {r: [] for r in r_values}

print("Running simulations...")
for r in r_values:
    for N in n_values:
        experiment_errors = np.zeros(num_experiments)
        experiment_stds = np.zeros(num_experiments)

        for i in range(num_experiments):
            # Generate swarm and colors
            positions = np.random.uniform(0, 1, size=(N, 2))
            colors = np.random.choice([0, 1], size=N) # 1 for black, 0 for white
            actual_black = np.sum(colors)

            # find neighbors
            distances = cdist(positions, positions)
            neighborhoods = (distances < r)

            # estimates
            black_in_hood = np.sum(neighborhoods * colors, axis=1)
            total_in_hood = np.sum(neighborhoods, axis=1)

            # avoid division by zero
            local_ratios = np.divide(black_in_hood, total_in_hood, out=np.zeros_like(total_in_hood, dtype=float), where=total_in_hood!=0)

            # robots estimate of total black robots
            estimates = local_ratios * N

            # Calculate how far off the average swarm estimate is from the actual truth
            mean_swarm_estimate = np.mean(estimates)
            experiment_errors[i] = np.abs(mean_swarm_estimate - actual_black) / max(actual_black, 1) # Relative error
            
            # Calculate the standard deviation between the robots in this specific swarm
            experiment_stds[i] = np.std(estimates)
            
        # Store the average results across the 1000 experiments for this N and r
        mean_estimates_error[r].append(np.mean(experiment_errors))
        std_estimates[r].append(np.mean(experiment_stds))

print("Plotting results...")

# Plotting
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

fig.patch.set_facecolor('black')
for ax in [ax1, ax2]:
    ax.set_facecolor('black')
    ax.grid(color='yellow', linestyle='--', alpha=0.3)
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

colors_plot = ['cyan', 'magenta', 'lime', 'orange']

for idx, r in enumerate(r_values):
    ax1.plot(n_values, mean_estimates_error[r], color=colors_plot[idx], linewidth=2, label=f'r = {r}')
    ax2.plot(n_values, std_estimates[r], color=colors_plot[idx], linewidth=2, label=f'r = {r}')

ax1.set_title("Mean Relative Error of Swarm Estimate\n(Lower is more accurate)")
ax1.set_xlabel("Swarm Size ($N$)")
ax1.set_ylabel("Relative Error")
ax1.legend(facecolor='white', framealpha=0.9)

ax2.set_title("Standard Deviation of Estimates within the Swarm\n(Lower means robots agree with each other)")
ax2.set_xlabel("Swarm Size ($N$)")
ax2.set_ylabel("Standard Deviation of Estimates")
ax2.legend(facecolor='white', framealpha=0.9)

plt.tight_layout()
plt.savefig("CollRob_03_GANDHI_MACHIDA/Task 3/plots/3_mean_error_and_std_vs_n.png")
plt.show()