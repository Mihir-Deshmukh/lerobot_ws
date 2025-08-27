import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    # Path to other launch files
    lerobot_description_launch = os.path.join(
        get_package_share_directory('lerobot_description'),
        'launch/so101_gazebo.launch.py')

    lerobot_controller_launch = os.path.join(
        get_package_share_directory('lerobot_controller'),
        'launch/so101_controller.launch.py')
        
    lerobot_moveit_launch = os.path.join(
        get_package_share_directory('lerobot_moveit'),
        'launch/so101_moveit.launch.py')

    # 1. Launch Gazebo simulation
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lerobot_description_launch),
    )

    # 2. After a 5-second delay, launch the controllers
    controllers_launch_delayed = TimerAction(
        period=8.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(lerobot_controller_launch),
            )
        ]
    )
    
    # 3. Launch MoveIt
    moveit_launch_delayed = TimerAction(
        period=15.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(lerobot_moveit_launch),
            )
        ]
    )

    return LaunchDescription([
        gazebo_launch,
        controllers_launch_delayed,
        moveit_launch_delayed,
    ])