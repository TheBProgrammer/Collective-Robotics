# Task 3 — Foraging

A foraging controller for ARGoS foot-bots. Robots search the arena for objects,
push them into a home zone marked by a bright light, and go back out. We measure
swarm performance (objects collected in a fixed period) over swarm size
`N = 1..10`.

## Running

Everything runs inside the ARGoS container.

```bash
./run_docker.sh build         # build the ARGoS image (once, ~15 min)
./run_docker.sh loop          # compile the loop functions -> libforaging_loop.so
./run_docker.sh gui           # watch a single simulation (needs X11)
./run_docker.sh experiments   # full sweep: 10 sizes x 10 reps, ~1.5 min
./run_docker.sh plot          # write the figures to plots/
```

`experiments` and `plot` also work outside the container if you have `argos3`
on your PATH (and, for plotting, numpy/pandas/matplotlib):

```bash
python3 run_experiments.py && python3 plot_results.py
```

## Files

| File | Purpose |
| --- | --- |
| `task3.argos` | arena, home light, 40 objects, robots, loop functions |
| `foraging.lua` | the robot controller |
| `foraging_loop.cpp` | ground-truth scoring + object respawn |
| `run_experiments.py` | sweeps `N = 1..10`, writes `data/` |
| `plot_results.py` | writes `plots/` |

## The setup

A 4 m × 4 m arena. A bright yellow light at `(-1.75, 0)` marks the home zone.
Forty movable cylinders, each carrying a blue LED, start in the eastern part of
the arena. The robots start on the home side.

An object counts as **collected** once its centre comes within 0.35 m of the
light (`home_radius` in `task3.argos`). The loop functions then respawn it at a
random spot in the foraging field. Respawning does two things: the swarm never
runs out of resource during the observation window, and delivered objects never
pile up at the edge of the home zone where they would sit inside the robots'
camera range and corrupt the object count.

The deposit radius and the controller's light thresholds are coupled: an object
is harvested while the robot pushing it is still ~0.52 m out, so the robot has
to recognise the delivery at that distance. Changing `home_radius` means
recalibrating `NEAR_HOME` and `HOME_LIGHT` in `foraging.lua` against the
light-sum table below.

## The controller

Five states: `SEARCH` → `APPROACH` → `TRANSPORT` → `BACKUP` → `TURN` → `SEARCH`.

* **SEARCH** — random walk with obstacle avoidance. Inside the home zone the
  robot walks away from the light instead, and ignores objects, so it does not
  re-harvest the nest.
* **APPROACH** — steer towards the nearest blue blob until the bumper presses.
* **TRANSPORT** — push towards the light. Obstacle repulsion skips the front
  arc, so the robot does not steer away from the object it is pushing.
* **BACKUP** / **TURN** — reverse and turn away after a delivery.

Two details that matter:

**Delivery is decided on the falling edge of contact.** The tick the object
leaves the bumper is the only moment that says anything about where it went. If
the robot instead waits and checks "am I near the light now?", it coasts towards
the nest after dropping an object halfway and claims a delivery it never made —
that alone inflated the robots' self-reported count by 36 %.

**A stuck robot abandons its object.** A robot that pushes an object into the
wall *beside* the nest would push forever: the object never enters the home
zone, so contact is never lost. The `error` output detects this (commanded to
move, but no travel), and after 10 further cycles the robot backs off and
resumes searching.

### The bumper

ARGoS has no force/bumper sensor, so the sheet's bumper is emulated from the
proximity ring plus the camera. On this build, an object straight ahead reads:

| distance | proximity |
| --- | --- |
| 16.5 cm (touching) | 1.00 |
| 19 cm | 0.37 |
| 25 cm | 0.11 |
| 35 cm | 0.00 |

So the ring fires well before contact. The bumper is *pressed* when proximity
exceeds `0.35` **and** the camera sees an object blob within `18.5 cm` in the
front arc. The measured **force** is the number of such blobs, i.e. how many
objects are being pushed.

### The six required outputs

Logged every 10 ticks as a `DATA,...` line. Flags are `1` (true), `0` (false),
`-1` (unknown).

| Output | How it is derived |
| --- | --- |
| motor left/right | commanded wheel velocities |
| error | stuck detector: commanded to move but travelled < 2 cm in 3 s (`unknown` until the history buffer fills) |
| collision | strongest proximity hit is best explained by a range-and-bearing neighbour |
| arena boundary | the hit is explained by neither a neighbour nor an object blob |
| transporting object | the robot is in `TRANSPORT` |
| home zone | sum of the 24 light readings > 4.21 (≈ 0.35 m from the light) |

Light sum against distance from the home light, measured on this build:

| distance | 0.20 | 0.35 | 0.45 | 0.50 | 0.55 | 0.65 | 0.70 | 1.00 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| light sum | 4.45 | 4.21 | 4.02 | 3.92 | 3.81 | 3.61 | 3.51 | 2.93 |

A proximity hit can have several explanations at once, so `collision` and
`boundary` are decided by whichever candidate — neighbour or object — is
*nearer* to the reported bearing. Sanity check from the sweep: when
`collision = 1` the mean distance to the nearest other robot is 0.19 m (foot-bot
contact is ~0.17 m) versus 0.48 m otherwise, and at `N = 1` the flag never fires.

## Results

10 swarm sizes × 20 repetitions × 300 s.

Swarm performance grows **sublinearly**: a power-law fit over `N >= 2` gives
`collected ∝ N^0.78`. Per-robot performance falls from 1.65 objects at `N = 2`
to 1.08 at `N = 10` — classic interference. Robot–robot collisions rise roughly
linearly with `N` and account for the loss.

| N | collected (300 s) | per robot | collisions |
| --- | --- | --- | --- |
| 1 | 1.3 ± 0.7 | 1.30 | 0.0 % |
| 2 | 3.3 ± 1.2 | 1.65 | 5.1 % |
| 5 | 6.9 ± 1.7 | 1.38 | 15.3 % |
| 10 | 10.8 ± 2.5 | 1.08 | 22.5 % |

Note that per-robot performance *rises* from `N = 1` to `N = 2` before it starts
to fall. A lone robot is not merely a swarm of one: it has no team-mate to
happen upon an object it walked past, and when it gets stuck it loses a large
share of its 300 s with nobody to compensate. The single-robot rate is therefore
a poor baseline for an "ideal linear" reference, and the plot fits the exponent
instead of extrapolating from `N = 1`.

The robots' own camera-based delivery count now agrees with the ground truth to
within 2 %. Performance is nevertheless scored from the simulator: the agreement
is a property of a carefully chosen threshold, not something a real swarm could
rely on.
