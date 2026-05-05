import math
# import pygame
import numpy as np
from firefly import Firefly
import matplotlib.pyplot as plt

# Constants
NUM_FIREFLIES = 150
L = 50
R = 0.1
TIME_STEPS = 5000
VISUALIZE = False

# Create a list of fireflies
fireflies = [Firefly(L) for _ in range(NUM_FIREFLIES)]

# Initialize pygame
# TODO: Implement pygame initialization

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
plt.plot(flashing_history)
plt.xlabel("Time Steps")
plt.ylabel("Number of Flashing Fireflies")
plt.title("Number of Flashing Fireflies over Time")
plt.show()