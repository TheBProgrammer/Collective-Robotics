# uav-path-planning

## Quick start

```bash
# Host: start the Docker container
cd ~/ros2_ws
./scripts/start.sh

# Inside the container: launch simulation + navigation
./scripts/launch_sim.sh

# Open a second terminal inside the running container
./scripts/shell.sh

# Stop and exit the container
exit
```

## Package overview

| Package | Contents |
|---|---|
| `uav_gazebo` | Gazebo sim nodes (`position_controller`, `odom_to_tf`, `pointcloud_relay`), forest worlds, tree models |
| `uav_navigation` | Path planning server, path follower, collision monitor |
| `uav_description` | Robot URDF/SDF |
| `uav_bringup` | Top-level launch files |
| `uav_benchmarks` | Evaluation / benchmarking tools |

## uav_navigation — key files

```
uav_navigation/
├── include/uav_navigation/
│   └── planners/
│       ├── planner_interface.hpp   ← pluginlib base class
│       ├── astar_planner.hpp
│       └── dstar_lite_planner.hpp
├── src/
│   ├── planners/
│   │   ├── astar_planner.cpp
│   │   └── dstar_lite_planner.cpp
│   ├── planner_server_node.cpp
│   ├── path_follower_node.cpp
│   └── collision_monitor_node.cpp
├── config/
│   └── uav_nav_params.yaml         ← all tunable parameters in one file
├── launch/
│   └── navigation.launch.py
└── plugins.xml                     ← pluginlib planner registry
```

All navigation parameters live in `config/uav_nav_params.yaml`,
namespaced per node (`planner_server`, `path_follower`, `collision_monitor`).

### Switching planners

Pass `planner_type` at launch or edit `uav_nav_params.yaml`:

```bash
ros2 launch uav_navigation navigation.launch.py planner_type:=astar
ros2 launch uav_navigation navigation.launch.py planner_type:=dstar_lite
```

Planners are loaded at runtime via pluginlib — adding a new planner
only requires a new shared library entry in `plugins.xml`; the server
node does not need to be recompiled.

## Utilities

```bash
# Send a velocity command directly to the drone
gz topic -t /X3/cmd_vel -m gz.msgs.Twist -p '
linear: {x: 0.0, y: 0.0, z: 1.0}
angular: {z: 0.0}
'

# Plot trajectory
ros2 run plotjuggler plotjuggler

# Generate procedural forest worlds
python3 src/uav_gazebo/scripts/gen_worlds.py \
    --num_worlds 10 --world_length 10 --tree_density 0.1 --max_height 0
python3 src/uav_gazebo/scripts/gen_worlds.py \
    --num_worlds 10 --world_length 10 --tree_density 0.1 --max_height 1.0
```