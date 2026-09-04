import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    """MoveIt bringup for the Gazebo simulation (group_1_ names, sim controllers)."""
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true')
    use_sim_time = LaunchConfiguration('use_sim_time')

    package_share = get_package_share_directory('motoman_hc10dtp_b00_moveit2_config')
    robot_description_file_path = os.path.join(
        package_share, 'config', 'motoman_hc10dtp_b00_sim.urdf.xacro'
    )
    robot_description_semantic_file_path = os.path.join(
        package_share, 'config', 'motoman_hc10dtp_b00_sim.srdf'
    )
    trajectory_execution_file_path = os.path.join(
        package_share, 'config', 'moveit_controllers_sim.yaml'
    )
    joint_limits_file_path = os.path.join(package_share, 'config', 'joint_limits_sim.yaml')
    rviz_config_file_path = os.path.join(package_share, 'config', 'moveit_sim.rviz')

    moveit_config = (
        MoveItConfigsBuilder(
            'motoman_hc10dtp_b00',
            package_name='motoman_hc10dtp_b00_moveit2_config',
        )
        .robot_description(file_path=robot_description_file_path)
        .robot_description_semantic(file_path=robot_description_semantic_file_path)
        .trajectory_execution(file_path=trajectory_execution_file_path)
        .joint_limits(file_path=joint_limits_file_path)
        .to_moveit_configs()
    )

    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[moveit_config.to_dict(), {'use_sim_time': use_sim_time}],
        arguments=['--ros-args', '--log-level', 'info'],
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config_file_path],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            {'use_sim_time': use_sim_time},
        ],
    )

    # robot_state_publisher is already started by motoman_hc10_support/launch/gazebo.launch.py.
    return LaunchDescription([use_sim_time_arg, move_group_node, rviz_node])
