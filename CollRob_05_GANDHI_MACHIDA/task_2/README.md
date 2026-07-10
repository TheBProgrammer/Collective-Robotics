# Task 2 — Density-Dependent Global Switching

Do the simulated locusts switch their collective direction more often at low
density, as real ones do?

## Running

```bash
python task_2.py        # ~6 min on 8 cores
```

Needs `numpy`, `scipy`, `matplotlib`. Writes `plots/task_2_switching.png` and
`task_2_results.npz`.

## Method

The locust simulation lives in `../locust.py` and is shared with task 1. Task 2
uses the task-1 parameter set (`C = 0.5`, speed `0.01`, `r = 0.045`,
`P = 0.15`) and varies only the swarm size, `N ∈ [20, 150]`.

Three zones on the left-goer count `L`:

```
Zone A: L > 0.7 N        Zone B: 0.3 N <= L <= 0.7 N        Zone C: L < 0.3 N
```

A global switch is a B-crossing that connects A to C (or C to A). While the
swarm sits in A or C the counter is zero; entering B starts it; leaving B into
the opposite zone stores the counter; leaving B back the way it came resets it.

Each of the 10 swarm sizes is run 10 times for **200,000 time steps** — far more
than the 5,000 the sheet asks for, because switches become very rare at large
`N`. All sizes use the same number of steps, so the switch *counts* are directly
comparable.

A run that starts inside zone B is not counted until it has first touched A or
C, since until then there is no zone of origin.

## Two different quantities

The sheet's counter measures the time spent *inside zone B* during a crossing.
That is not the same as the time *between* switches, and only the latter carries
the density dependence:

| N | switches (2M steps) | crossing time | waiting time |
| --- | --- | --- | --- |
| 20 | 16759 | 11.8 | 119 |
| 50 | 3476 | 11.9 | 575 |
| 80 | 881 | 11.3 | 2252 |
| 110 | 100 | 11.2 | 19001 |
| 130 | 27 | 11.3 | 46127 |
| 150 | 2 | 12.5 | — |

So we report both. The crossing time is flat at ~11–13 steps for every swarm
size: once the swarm is disorganised enough to be in zone B, it takes about the
same time to fall into one of the two attractors regardless of `N`.

The waiting time between switches grows by a factor of ~400 from `N = 20` to
`N = 130`, and the number of observed switches collapses from 16759 to 2. At
`N = 150` we saw only two switches in two million time steps and no run
contained two of them, so no waiting time can be reported.

## Result

Yes — the simulation reproduces the biological observation. A dense swarm
locks into its chosen direction and almost never flips; a sparse swarm flips
constantly. The mechanism is that alignment is driven by the local majority, and
a larger swarm means more neighbours per locust, so the spontaneous flips
(probability `P = 0.15` each) are far less likely to overcome the majority all
at once.
