# Collective Robotics — Tutorial 5

Gandhi, Machida — Collective Decision-Making: Urn Model, Global Switching, Foraging

## Layout

```
locust.py          shared locust simulation (tasks 1 and 2)
task_1/            urn model for the locust scenario
task_2/            density-dependent global switching
task_3/            foraging in ARGoS
report.tex         the report
```

## The shared locust simulation

`locust.py` is the continuous-space, discrete-time locust model from tutorial 4,
task 1 — same two switching rules — but parameterized, since tutorial 5 uses a
different parameter set (`C = 0.5`, speed `0.01`, `N = 50`, `P = 0.15`) and task
2 sweeps `N`.

```python
from locust import simulate
L = simulate(N=50, T=120, C=0.5, speed=0.01, r=0.045, p=0.15, seed=0)
# -> array of left-goer counts, length T + 1
```

Two changes were needed relative to the tutorial-4 code:

* **The ring circumference was hard-coded.** The old `step()` computed
  `np.minimum(distances, 1 - distances)` and seeded positions with
  `np.random.uniform(0, 1, n)`, both assuming `C = 1`. With `C = 0.5` that would
  have placed half the locusts off the ring and computed wrong wrap-around
  distances.
* **It was too slow.** The per-locust Python loop is replaced by a pairwise
  distance matrix. Task 1 needs 5,000 runs and task 2 needs runs of 200,000
  steps, which the original code could not deliver in reasonable time. The
  distance matrix is built in float32 (it dominates the runtime and float64
  spills out of L2 cache); positions stay float64 so the integration does not
  drift over millions of steps.

The vectorized majority rule was checked to agree *exactly* with the tutorial-4
implementation on 200 random swarm states, and the distribution of the final
left-goer count agrees under a two-sample KS test.

## Running

Tasks 1 and 2 are plain Python (`numpy`, `scipy`, `matplotlib`):

```bash
python task_1/task_1.py     # see task_1/README.md
python task_2/task_2.py     # ~6 min on 8 cores
```

Task 3 runs in Docker, since it needs ARGoS:

```bash
cd task_3
./run_docker.sh build && ./run_docker.sh loop
./run_docker.sh experiments && ./run_docker.sh plot
```

See `task_2/README.md` and `task_3/README.md` for details and results.
