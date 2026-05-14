# Collective Robotics - Tutorial 1: Task 1

## Scaling of a Computer System

### Group Members

- Bhavesh Gandhi, Jaqueline Machida

# Overview

Models a computer job queue using a Poisson arrival process and measures how average queue length scales with arrival rate.

## Requirements

Python 3.x with `matplotlib` (standard library only otherwise).

```bash
pip install matplotlib
```

## How to Run

Run each subtask script from inside the `task_1/` directory:

```bash
cd task_1/

python task1a.py
python task1b.py
python task1c.py
python task1d.py
python task1e.py
```

Each script saves its plot as a PNG in the same directory.

## Files

| File | Description |
|------|-------------|
| `queue_model.py` | Core module: Poisson PMF, sampler, and queue simulation |
| `task1a.py` | Subtask a: PMF plots |
| `task1b.py` | Subtask b: sampling demonstration |
| `task1c.py` | Subtask c: single simulation run |
| `task1d.py` | Subtask d: average queue vs α (processing duration = 4) |
| `task1e.py` | Subtask e: comparison of 4-step vs 2-step processing |