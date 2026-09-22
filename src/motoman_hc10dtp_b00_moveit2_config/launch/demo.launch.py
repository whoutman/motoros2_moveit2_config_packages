import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    db_arg = DeclareLaunchArgument(
        "warehouse_host", default_value="", description="Database connection path"
    )
    use_sim_time_arg = DeclareLaunchArgument("use_sim_time", default_value="true")
    use_sim_time = LaunchConfiguration("use_sim_time")
    log_level_arg = DeclareLaunchArgument("log_level", default_value="info")
    log_level = LaunchConfiguration("log_level")

    package_share = get_package_share_directory("motoman_hc10dtp_b00_moveit2_config")
    robot_description_file_path = os.path.join(
        package_share, "config", "motoman_hc10dtp_b00.urdf.xacro"
    )
    robot_description_semantic_file_path = os.path.join(
        package_share, "config", "motoman_hc10dtp_b00.srdf"
    )
    trajectory_execution_file_path = os.path.join(
        package_share, "config", "moveit_controllers.yaml"
    )
    rviz_config_file_path = os.path.join(package_share, "config", "moveit.rviz")

    robot_description_contents = xacro.process_file(robot_description_file_path).toxml()
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
        .planning_pipelines(default_planning_pipeline="ompl", pipelines=["ompl"])
        .to_moveit_configs()
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            warehouse_ros_config,
            {"use_sim_time": use_sim_time},
        ],
        arguments=[
            "--ros-args",
            "--log-level",
            log_level,
            # silence high-frequency rcl/rmw/rclcpp internals even when log_level=debug
            "--log-level",
            "rcl:=warn",
            "--log-level",
            "rclcpp:=warn",
            "--log-level",
            "rmw_fastrtps_cpp:=warn",
        ],
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
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[
            {
                "robot_description": robot_description_contents,
                "use_sim_time": use_sim_time,
            }
        ],
    )

    return LaunchDescription(
        [db_arg, use_sim_time_arg, log_level_arg, move_group_node, rviz_node, robot_state_publisher_node]
    )
