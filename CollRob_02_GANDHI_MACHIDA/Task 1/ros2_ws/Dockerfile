FROM osrf/ros:jazzy-desktop

# Install ROS–Gazebo integration (ros_gz) and build tools
RUN apt-get update && apt-get install -y \
    python3-transforms3d \
    python3-pandas \
    ros-jazzy-tf-transformations \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-sim-demos \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-gz-sim-vendor \
    ros-jazzy-depth-image-proc \
    ros-jazzy-octomap-server \
    ros-jazzy-plotjuggler-ros \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# Set Gazebo plugin paths - the vendor package installs to /opt/ros/jazzy
ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/opt/ros/jazzy/opt/gz-sim-8/lib/gz-sim-8/plugins:/opt/ros/jazzy/lib/gz-sim-8/plugins:${GZ_SIM_SYSTEM_PLUGIN_PATH}
ENV GZ_SIM_RESOURCE_PATH=/opt/ros/jazzy/share/gz-sim-8:${GZ_SIM_RESOURCE_PATH}

# Source ROS setup
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

# Workspace inside container
WORKDIR /root/ros2_ws
COPY ./src ./src