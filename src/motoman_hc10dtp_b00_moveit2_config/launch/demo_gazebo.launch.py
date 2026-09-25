import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    """MoveIt bringup for the Gazebo simulation (group_1_ names, sim controllers)."""
    db_arg = DeclareLaunchArgument(
        "warehouse_host", default_value="", description="Database connection path"
    )
    use_sim_time_arg = DeclareLaunchArgument("use_sim_time", default_value="true")
    use_sim_time = LaunchConfiguration("use_sim_time")

    package_share = get_package_share_directory("motoman_hc10dtp_b00_moveit2_config")
    robot_description_file_path = os.path.join(
        package_share, "config", "motoman_hc10dtp_b00_sim.urdf.xacro"
    )
    robot_description_semantic_file_path = os.path.join(
        package_share, "config", "motoman_hc10dtp_b00_sim.srdf"
    )
    trajectory_execution_file_path = os.path.join(
        package_share, "config", "moveit_controllers_sim.yaml"
    )
    joint_limits_file_path = os.path.join(package_share, "config", "joint_limits_sim.yaml")
    rviz_config_file_path = os.path.join(package_share, "config", "moveit_sim.rviz")

    warehouse_ros_config = {
        "warehouse_plugin": "warehouse_ros_sqlite::DatabaseConnection",
        "warehouse_host": LaunchConfiguration("warehouse_host"),
    }

    moveit_config = (
        MoveItConfigsBuilder(
            "motoman_hc10dtp_b00",
            package_name="motoman_hc10dtp_b00_moveit2_config",
        )
        .robot_description(file_path=robot_description_file_path)
        .robot_description_semantic(file_path=robot_description_semantic_file_path)
        .trajectory_execution(file_path=trajectory_execution_file_path)
        .joint_limits(file_path=joint_limits_file_path)
        .to_moveit_configs()
    )

    # Applies to every node in this process, including the internal MoveGroupInterface
    # node that RViz's Context-tab DB connect spins up for path-constraint storage.
    set_warehouse_plugin_param = SetParameter(
        name="warehouse_plugin", value="warehouse_ros_sqlite::DatabaseConnection"
    )
    set_warehouse_host_param = SetParameter(name="warehouse_host", value=LaunchConfiguration("warehouse_host"))

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict(), warehouse_ros_config, {"use_sim_time": use_sim_time}],
        arguments=["--ros-args", "--log-level", "info"],
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file_path],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            warehouse_ros_config,
            {"use_sim_time": use_sim_time},
        ],
    )

    # robot_state_publisher is already started by motoman_hc10_support/launch/gazebo.launch.py.
    return LaunchDescription(
        [
            db_arg,
            use_sim_time_arg,
            set_warehouse_plugin_param,
            set_warehouse_host_param,
            move_group_node,
            rviz_node,
        ]
    )
