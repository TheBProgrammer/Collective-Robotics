import math
import numpy as np
from firefly import Firefly
import matplotlib.pyplot as plt

# Constants
NUM_FIREFLIES = 150
L = 50
TIME_STEPS = 5000
NUM_SAMPLES = 50
R_VALS = np.arange(0.025, 1.4 + 0.025, 0.025)

# Store data
average_amplitudes = []

print(f"Running {len(R_VALS)} r values × {NUM_SAMPLES} samples = {len(R_VALS) * NUM_SAMPLES} total simulations")
print("This may take a few minutes...\n")

for r_idx, R in enumerate(R_VALS):
    print(f"Progress: {r_idx + 1}/{len(R_VALS)},  R = {R:.3f}")

    amplitudes_for_R = []
    
    # Run 50 independent sims
    for sample in range(NUM_SAMPLES):
        # Create a list of fireflies
        fireflies = [Firefly(L) for _ in range(NUM_FIREFLIES)]

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

        # Extract last 50 steps
        last_cycle = flashing_history[-50:]

        # Calculate amplitude of the last cycle
        amplitude = np.max(last_cycle) - np.min(last_cycle)
        amplitudes_for_R.append(amplitude)
    
    # Average the amplitudes
    avg_amplitude = np.mean(amplitudes_for_R)
    average_amplitudes.append(avg_amplitude)

print("\n All Simulations Complete!")

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(R_VALS, average_amplitudes, 'b-', linewidth=2)
plt.xlabel('Vicinity Radius (r)', fontsize=12)
plt.ylabel('Average Amplitude', fontsize=12)
plt.title('Synchronization Quality vs Vicinity Radius', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('./Assignment_1/task_2/task2b_amplitude_vs_radius.png', dpi=300, bbox_inches='tight')
plt.show()

print("Plot saved as 'task2b_amplitude_vs_radius.png'")