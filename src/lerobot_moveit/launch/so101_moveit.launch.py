import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration

from launch_ros.actions import Node
import launch_param_builder

# Workaround: ensure load_xacro passes a string filename to xacro.process_file.
# Some xacro versions don't accept pathlib.Path for input_file_name, which causes
# a TypeError during MoveItConfigsBuilder.robot_description(). Patch the
# function at runtime (in the launch_param_builder package) so it accepts Path
# and forwards a str to xacro before MoveItConfigsBuilder imports it.
def _load_xacro_compat(file_path, mappings=None):
    # reuse existing checks
    launch_param_builder.raise_if_file_not_found(file_path)
    import xacro
    # Some xacro versions call re.sub on the input filename and expect a str.
    # Protect against pathlib.Path by ensuring the filename passed to xacro is a str.
    _orig_process = getattr(xacro, 'process_file')
    def _process_compat(input_file_name, mappings=None, **kwargs):
        return _orig_process(str(input_file_name), mappings=mappings, **kwargs)
    xacro.process_file = _process_compat
    file = xacro.process_file(str(file_path), mappings=mappings)
    return file.toxml()

launch_param_builder.load_xacro = _load_xacro_compat

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    # create a runtime lauch argument
    is_sim_arg = DeclareLaunchArgument(name="is_sim", default_value="True")

    # get the argument value at runtime
    is_sim = LaunchConfiguration("is_sim")

    # URDF and MoveIt config files (use absolute paths to avoid Path objects)
    lerobot_description_dir = get_package_share_directory("lerobot_description")
    so101_urdf_path = os.path.join(lerobot_description_dir, "urdf", "so101.urdf.xacro")

    lerobot_moveit_dir = get_package_share_directory("lerobot_moveit")
    so101_srdf_path = os.path.join(lerobot_moveit_dir, "config", "so101.srdf")
    moveit_controllers_path = os.path.join(lerobot_moveit_dir, "config", "moveit_controllers.yaml")

    moveit_config = (
        MoveItConfigsBuilder("so101", package_name="lerobot_moveit")
        .robot_description(file_path=str(so101_urdf_path))
        .robot_description_semantic(file_path=str(so101_srdf_path))
        .trajectory_execution(file_path=str(moveit_controllers_path))
        .to_moveit_configs()
    )

    # moveit core
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
    # pass a serializable dict for MoveIt configs to avoid PosixPath in parameters
    parameters=[moveit_config.to_dict(), {"use_sim_time": is_sim}, {"publish_robot_description_semantic": True}],
        arguments=["--ros-args", "--log-level", "info"]
    )

    rviz_config_path = os.path.join(get_package_share_directory("lerobot_moveit"),"config", "grasp.rviz")

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
    # pass a serializable dict for MoveIt configs to avoid PosixPath in parameters
    parameters=[moveit_config.to_dict()]
    )

    return LaunchDescription([
        is_sim_arg,
        move_group_node,
        rviz_node
    ])
