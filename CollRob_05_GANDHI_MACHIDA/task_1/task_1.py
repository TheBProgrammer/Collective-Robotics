import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tqdm import tqdm

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from locust import simulate, N

def collect_urn_data(runs=5000, warmup=100, observation=20):
    '''Runs the locust simulation and collects empirical delta L data'''
    T = warmup + observation

    # Bins to accumulate total delta_L and occurrences for every possible L state (0 to N)
    delta_L_sums = np.zeros(N + 1)
    L_counts = np.zeros(N + 1)

    for _ in tqdm(range(runs), desc="Simulation Swarm Runs"):
        # simulate() returns an array of length T+1
        counts = simulate(T=T)
        
        # Slicing out the observation window
        L_prev = counts[warmup : warmup + observation]
        L_curr = counts[warmup + 1 : warmup + observation + 1]
        
        delta_L = L_curr - L_prev
        
        # Accumulate sums and counts for each state
        for prev, delta in zip(L_prev, delta_L):
            delta_L_sums[prev] += delta
            L_counts[prev] += 1
            
    # Calculate the mean delta L for each L
    with np.errstate(invalid='ignore'):
        avg_delta_L = np.divide(delta_L_sums, L_counts)
        
    return avg_delta_L, L_counts

# Curve Fitting 
def p_fb(s, phi):
    '''Probability of positive feedback.'''
    return phi * np.sin(np.pi * s)

def urn_model_delta_s(s, c, phi):
    """
    The theoretical expected change in ratio s, derived from the Urn Model - Equation 3 from the assignment
    """
    return 4 * c * (p_fb(s, phi) - 0.5) * (s - 0.5)

# Analysis & Plotting Execution
def analyze_and_plot():
    # Generate the data
    avg_delta_L, L_counts = collect_urn_data()
    
    # We only fit over states that were actually visited to avoid NaNs
    valid_indices = ~np.isnan(avg_delta_L)
    L_valid = np.arange(N + 1)[valid_indices]
    delta_L_valid = avg_delta_L[valid_indices]
    
    # Convert absolute counts L to ratios s
    s_empirical = L_valid / N
    delta_s_empirical = delta_L_valid / N
    
    # Fit the data
    # We constrain bounds: c > 0, and phi between [0, 1]
    popt, pcov = curve_fit(
        urn_model_delta_s, 
        s_empirical, 
        delta_s_empirical, 
        bounds=([0, 0], [np.inf, 1.0])
    )
    
    c_opt, phi_opt = popt
    print(f"Fitted Parameters:\n Scaling Constant (c) = {c_opt:.4f}\n Feedback Intensity (phi) = {phi_opt:.4f}")
    
    # Generate smooth curves for the theoretical fit
    s_continuous = np.linspace(0, 1, 100)
    delta_s_fit = urn_model_delta_s(s_continuous, c_opt, phi_opt)
    p_fb_fit = p_fb(s_continuous, phi_opt)
    
    # Plotting
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Empirical Data vs Fitted Urn Model
    axes[0].scatter(s_empirical, delta_s_empirical, color='royalblue', label='Empirical Data', alpha=0.7)
    axes[0].plot(s_continuous, delta_s_fit, color='darkorange', linewidth=2, label=f'Urn Fit (c={c_opt:.2f}, \u03c6={phi_opt:.2f})')
    axes[0].axhline(0, color='black', linestyle='--', linewidth=1)
    axes[0].set_xlabel('Ratio of Left-Goers (s = L/N)')
    axes[0].set_ylabel('Expected Change (\u0394s)')
    axes[0].set_title('Expected State Change vs. State')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Probability of Positive Feedback
    axes[1].plot(s_continuous, p_fb_fit, color='forestgreen', linewidth=2, label=f'$P_{{FB}}$ (\u03c6={phi_opt:.2f})')
    axes[1].axhline(0.5, color='black', linestyle='--', linewidth=1, label='Neutral Threshold')
    axes[1].set_xlabel('Ratio of Left-Goers (s = L/N)')
    axes[1].set_ylabel('Probability of Positive Feedback ($P_{FB}$)')
    axes[1].set_title('Positive Feedback Profile')
    axes[1].set_ylim(0, 1.05)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("./plots/urn_model_analysis.png", dpi=300)
    plt.show()

if __name__ == "__main__":
    analyze_and_plot()