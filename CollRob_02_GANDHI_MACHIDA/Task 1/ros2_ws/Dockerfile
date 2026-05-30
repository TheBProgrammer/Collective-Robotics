FROM osrf/ros:jazzy-desktop

RUN apt-get update && apt-get install -y \
    ros-jazzy-ros-gz \
    python3-colcon-common-extensions \
    mesa-vulkan-drivers \
    libgl1-mesa-dri \
    && rm -rf /var/lib/apt/lists/*

# Gazebo Harmonic plugin and resource paths so ros-gz systems are found.
ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/opt/ros/jazzy/opt/gz-sim-8/lib/gz-sim-8/plugins:/opt/ros/jazzy/lib/gz-sim-8/plugins
ENV GZ_SIM_RESOURCE_PATH=/opt/ros/jazzy/share/gz-sim-8

RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

WORKDIR /root/ros2_ws
