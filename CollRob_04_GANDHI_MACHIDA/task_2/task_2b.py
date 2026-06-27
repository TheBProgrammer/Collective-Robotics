import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# params
ALPHA_R = 0.6       # collision (avoidance) rate
ALPHA_P = 0.2       # puck pick-up rate
TAU_A   = 2.0       # avoidance duration
TAU_H   = 15.0      # homing duration
NS0     = 1.0       # initial searching density
M0      = 1.0       # initial puck density
T_END   = 160.0     # final time
DT      = 0.01      # forward Euler step

def simulate_with_homing(t_end=T_END, dt=DT, reset_m_at=None, reset_m_value=None):
    n_steps     = int(round(t_end / dt))
    delay_a     = int(round(TAU_A / dt))
    delay_h     = int(round(TAU_H / dt))

    ns = np.zeros(n_steps + 1)
    nh = np.zeros(n_steps + 1)
    m  = np.zeros(n_steps + 1)
    ns[0] = NS0
    m[0]  = M0

    reset_idx = None
    if reset_m_at is not None:
        reset_idx = int(round(reset_m_at / dt))

    for k in range(n_steps):
        # delayed avoidance return: 0 for t < TAU_A
        if k - delay_a >= 0:
            ns_a = ns[k - delay_a]
            return_avoid = ALPHA_R * ns_a * (ns_a + 1.0)
        else:
            return_avoid = 0.0

        # delayed homing return: 0 for t < TAU_H
        if k - delay_h >= 0:
            ns_h = ns[k - delay_h]
            m_h  = m[k - delay_h]
            return_home = ALPHA_P * ns_h * m_h
        else:
            return_home = 0.0

        # instantaneous rates
        leave_avoid = ALPHA_R * ns[k] * (ns[k] + 1.0)
        leave_home  = ALPHA_P * ns[k] * m[k]

        dns = -leave_avoid + return_avoid - leave_home + return_home
        dnh =  leave_home  - return_home
        dm  = -leave_home

        ns[k + 1] = ns[k] + dt * dns
        nh[k + 1] = nh[k] + dt * dnh
        m[k + 1]  = m[k]  + dt * dm

        # forced reset of pucks
        if reset_idx is not None and k + 1 == reset_idx:
            m[k + 1] = reset_m_value

    t = np.linspace(0.0, t_end, n_steps + 1)
    return t, ns, nh, m

def plot_run(t, ns, nh, m, title, out_path):
    plt.figure(figsize=(10, 4))
    plt.plot(t, ns, label=r"$n_s(t)$ (searching)", color="steelblue")
    plt.plot(t, nh, label=r"$n_h(t)$ (homing)",    color="seagreen")
    plt.plot(t, m,  label=r"$m(t)$ (pucks)",       color="darkorange")
    plt.xlabel("Time $t$")
    plt.ylabel("Density")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.show()

def task_2b():
    plot_dir = Path(__file__).resolve().parent / "plots"
    plot_dir.mkdir(exist_ok=True)

    # Run 1: no puck reset
    t1, ns1, nh1, m1 = simulate_with_homing()
    plot_run(t1, ns1, nh1, m1,
             "Task 2b - Searching, homing, avoiding (no reset)",
             plot_dir / "task_2b_no_reset.png")

    # Run 2: pucks reset to 0.5 at t = 80
    t2, ns2, nh2, m2 = simulate_with_homing(reset_m_at=80.0, reset_m_value=0.5)
    plot_run(t2, ns2, nh2, m2,
             "Task 2b - Pucks reset to m(80) = 0.5",
             plot_dir / "task_2b_reset.png")

if __name__ == "__main__":
    task_2b()
