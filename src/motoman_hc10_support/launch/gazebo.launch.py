import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, SetEnvironmentVariable
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    gui = LaunchConfiguration("gui")
    package_share = get_package_share_directory("motoman_hc10_support")
    xacro_file = os.path.join(package_share, "urdf", "hc10dtp_b00_gazebo.xacro")
    controllers_file = os.path.join(package_share, "config", "hc10dtp_b00_controllers.yaml")

    robot_description = {
        "robot_description": ParameterValue(
            Command(["xacro ", xacro_file]),
            value_type=str,
        )
    }

    gz_sim_launch = os.path.join(
        get_package_share_directory("ros_gz_sim"),
        "launch",
        "gz_sim.launch.py",
    )

    gazebo_with_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={"gz_args": "-r empty.sdf"}.items(),
        condition=IfCondition(gui),
    )

    # "-s" runs the Gazebo server headless (no GUI client).
    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={"gz_args": "-r -s empty.sdf"}.items(),
        condition=UnlessCondition(gui),
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
        output="screen",
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "motoman_hc10dtp_b00"],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_trajectory_controller",
            "--controller-manager",
            "/controller_manager",
            "--param-file",
            controllers_file,
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("gui", default_value="true", description="Launch the Gazebo GUI client"),
            SetEnvironmentVariable(
                name="GZ_SIM_RESOURCE_PATH",
                value=os.path.dirname(package_share),
            ),
            gazebo_with_gui,
            gazebo_headless,
            clock_bridge,
            robot_state_publisher,
            RegisterEventHandler(
                OnProcessStart(
                    target_action=robot_state_publisher,
                    on_start=[spawn_robot],
                )
            ),
            RegisterEventHandler(
                OnProcessStart(
                    target_action=spawn_robot,
                    on_start=[joint_state_broadcaster, trajectory_controller],
                )
            ),
        ]
    )
