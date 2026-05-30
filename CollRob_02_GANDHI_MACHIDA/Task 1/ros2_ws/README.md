# Single-Robot Behaviors (ROS 2 Jazzy + Gazebo Harmonic)

Three reactive behaviors for a simulated vacuum-cleaner robot in the TurtleBot3
House world: **collision avoidance**, **wall following**, and **vacuum-cleaner
coverage**. Each behavior is a standalone ROS 2 node with its own launch file.

## Prerequisites

- Docker (the workspace is set up to run inside a containerized ROS 2 Jazzy /
  Gazebo Harmonic environment).

## Build & source

From the host:

```bash
cd ros2_ws
./scripts/start.sh       # brings up the container
```

Inside the container:

```bash
cd /root/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

After editing any node you can rebuild only the package:

```bash
colcon build --packages-select single_robot --symlink-install
```

## Running each behavior

Every launch file does the same setup: starts Gazebo on the TurtleBot3 House
world, spawns the vacuum cleaner model, starts the ROS and Gazebo bridge for
`/scan`, `/cmd_vel`, `/odom`, `/tf`, `/joint_states`  and then runs the node
for that behavior.

### 1. Collision avoidance

```bash
ros2 launch single_robot collision_avoidance.launch.py
```

The robot drives forward at constant speed and rotates in place toward the
freer side whenever an obstacle enters the front cone. Hysteresis on the
trigger/clear distances prevents chattering at the threshold.

### 2. Wall following

```bash
ros2 launch single_robot wall_follower.launch.py
```

The robot searches for a wall on its right, then maintains a target distance
(0.40 m) to that wall using a PD controller on the side-cone minimum. A
`CORNER_TURN` state rotates left in place when the front is blocked
(concave corner), and the PD controller naturally curls back toward the wall
at convex corners.

### 3. Vacuum cleaner

```bash
ros2 launch single_robot vacuum_cleaner.launch.py
```

The robot performs a back-and-forth lawnmower pattern:

1. **SWEEP**: drive forward until an obstacle appears in front.
2. **TURN_A**: rotate 90° toward the alternating side using odometry.
3. **SHIFT**: drive forward by one body width (0.34 m), or until blocked /
   timeout.
4. **TURN_B**: rotate another 90° in the same direction to reverse heading
   and start the next stripe.

The U-turn direction flips between cycles so consecutive shifts always
advance to the same side of the room, producing parallel stripes. Turns and
the SHIFT distance use proportional control so the motion stops cleanly
without overshoot.

## Customizing the spawn pose

Each launch file spawns the robot at a fixed `(x, y)` inside the house. Edit
the `spawn_vacuum` block of the corresponding launch file under
`src/single_robot/launch/` to start the robot in a different room.

## Tuning

All behavior parameters are class constants at the top of each node file under
`src/single_robot/single_robot/`. The most useful ones:

- `collision_avoidance_node.py`: `CRUISE_SPEED`, `TURN_SPEED`,
  `TRIGGER_DISTANCE`, `CLEAR_DISTANCE`.
- `wall_follower_node.py`: `TARGET_DISTANCE`, `KP`, `KD`, `CORNER_TRIGGER`.
- `vacuum_cleaner_node.py`: `FORWARD_SPEED`, `TURN_SPEED`, `BODY_WIDTH`,
  `KP_YAW`, `KP_SHIFT`, `SHIFT_TIMEOUT`.

After changes, rebuild with `colcon build --packages-select single_robot
--symlink-install` and relaunch.
