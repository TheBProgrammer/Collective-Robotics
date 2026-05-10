import math
# import pygame
import numpy as np
from firefly import Firefly
import matplotlib.pyplot as plt

# Constants
NUM_FIREFLIES = 150
L = 50
RADII = [0.05, 0.1, 0.5, 1.4]  
TIME_STEPS = 5000

# Helper function
def calculate_average_neighbors(fireflies, radius):
    """
    Calculate the average number of neighbors per firefly
    within the given radius
    """
    total_neighbors = 0
    for firefly in fireflies:
        for other_firefly in fireflies:
            if firefly == other_firefly:
                continue
            dx = firefly.x - other_firefly.x
            dy = firefly.y - other_firefly.y
            dist_sq = dx**2 + dy**2
            if dist_sq < radius**2:
                total_neighbors += 1
    return total_neighbors / len(fireflies)

# Create figure
fig, axes = plt.subplots(2, 2, figsize=(12,10))
axes = axes.flatten()

for idx, R in enumerate(RADII):
    print(f"\nSimulating with R = {R}")
    
    # Create a list of fireflies
    fireflies = [Firefly(L) for _ in range(NUM_FIREFLIES)]

    # Caluclate and print average neighbors
    avg_neighbors = calculate_average_neighbors(fireflies, R)
    print(f"Average number of neighbors: {avg_neighbors:.2f}\n")

    # data collection
    flashing_history = []

    # Main simulation loop
    for t in range(TIME_STEPS):
        fireflies_to_correct = []

        # Phase 1: Observation
        for firefly in fireflies:
            if firefly.should_check_neighbors():
                total_neighbors = 0
                flashing_neighbors = 0

                for other_firefly in fireflies:
                    # Exclude self
                    if firefly == other_firefly:
                        continue

                    # find distance
                    dx = firefly.x - other_firefly.x
                    dy = firefly.y - other_firefly.y
                    dist_sq = dx**2 + dy**2

                    # check if within R
                    if dist_sq < R**2:
                        total_neighbors += 1
                        if other_firefly.is_flashing():
                            flashing_neighbors += 1
                
                # Local Majority Rule
                if total_neighbors > 0 and flashing_neighbors > (total_neighbors / 2):
                    fireflies_to_correct.append(firefly)
        
        # Phase 2: Correction
        for firefly in fireflies_to_correct:
            firefly.corrects_clock()
            
        # Tick
        for firefly in fireflies:
            firefly.tick()
        
        # collect data
        current_flashing = sum(1 for f in fireflies if f.is_flashing())
        flashing_history.append(current_flashing)

    # Plotting
    axes[idx].plot(flashing_history, 'k-', linewidth=1.5)
    axes[idx].set_xlim([0, TIME_STEPS])
    axes[idx].set_ylim(0, NUM_FIREFLIES)
    axes[idx].set_xlabel('Time steps')
    axes[idx].set_ylabel('Number of flashing fireflies')
    axes[idx].set_title(f'R = {R}, Avg Neighbors = {avg_neighbors:.2f}')
    axes[idx].grid(True, alpha=0.3)

# Adjust layout and save
plt.tight_layout()
plt.savefig('task2a_flashing_over_time.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nPlot saved as 'task2a_flashing_over_time.png'")