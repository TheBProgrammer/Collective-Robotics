import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# params
ALPHA_R = 0.6       # collision (avoidance) rate
ALPHA_P = 0.2       # puck pick-up rate
TAU_A   = 2.0       # avoidance duration
NS0     = 1.0       # initial searching density
M0      = 1.0       # initial puck density
T_END   = 50.0      # final time
DT      = 0.01      # forward Euler step

def simulate_searching_avoiding(t_end=T_END, dt=DT):
    n_steps = int(round(t_end / dt))
    delay_steps = int(round(TAU_A / dt))

    ns = np.zeros(n_steps + 1)
    m  = np.zeros(n_steps + 1)
    ns[0] = NS0
    m[0]  = M0

    for k in range(n_steps):
        # for t < TAU_A, no avoiding robots have returned yet, so delay term = 0
        if k - delay_steps >= 0:
            ns_delay = ns[k - delay_steps]
            delay_term = ALPHA_R * ns_delay * (ns_delay + 1.0)
        else:
            delay_term = 0.0

        dns = -ALPHA_R * ns[k] * (ns[k] + 1.0) + delay_term
        dm  = -ALPHA_P * ns[k] * m[k]

        ns[k + 1] = ns[k] + dt * dns
        m[k + 1]  = m[k]  + dt * dm

    t = np.linspace(0.0, t_end, n_steps + 1)
    return t, ns, m

def task_2a():
    t, ns, m = simulate_searching_avoiding()

    plot_dir = Path(__file__).resolve().parent / "plots"
    plot_dir.mkdir(exist_ok=True)

    plt.figure(figsize=(10, 4))
    plt.plot(t, ns, label=r"$n_s(t)$ (searching)", color="steelblue")
    plt.plot(t, m,  label=r"$m(t)$ (pucks)",       color="darkorange")
    plt.xlabel("Time $t$")
    plt.ylabel("Density")
    plt.title("Task 2a - Searching and avoiding rate equations")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plot_dir / "task_2a.png", dpi=150)
    plt.show()

if __name__ == "__main__":
    task_2a()
