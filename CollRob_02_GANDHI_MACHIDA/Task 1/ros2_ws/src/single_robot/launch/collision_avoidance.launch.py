import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('single_robot')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    models_dir = os.path.join(pkg_share, 'models')
    world_file = os.path.join(pkg_share, 'worlds', 'turtlebot3_house.world')
    vacuum_sdf = os.path.join(models_dir, 'vacuum_cleaner', 'model.sdf')
    bridge_config = os.path.join(pkg_share, 'config', 'ros_gz_bridge.yaml')

    # Let Gazebo resolve model:// URIs from the package's models/ tree.
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=models_dir + os.pathsep + os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    spawn_vacuum = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-file', vacuum_sdf,
            '-name', 'vacuum_cleaner',
            '-x', '-1.0', '-y', '4.55', '-z', '0.05',
        ],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': bridge_config}],
        output='screen',
    )

    collision_avoidance = Node(
        package='single_robot',
        executable='collision_avoidance_node',
        name='collision_avoidance_node',
        output='screen',
    )

    return LaunchDescription([
        set_gz_resource_path,
        gz_sim,
        spawn_vacuum,
        bridge,
        collision_avoidance,
    ])
