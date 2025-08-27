#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration

from controller_manager_msgs.srv import SwitchController, ListControllers
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray

import sys
import time
import math

class RobotControllerCLI(Node):
    """
    A command-line interface for controlling the SO101 robot.
    """

    def __init__(self):
        super().__init__("robot_controller_cli")

        # --- Constants and Pre-defined Positions ---
        self.ARM_JOINT_NAMES = ["1", "2", "3", "4", "5"]
        self.GRIPPER_JOINT_NAME = ["6"]
        self.HOME_POSITION = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.READY_POSITION = [-0.3, -1.0, 1.2, -1.5, 0.0]
        self.GRIPPER_OPEN = [1.7]
        self.GRIPPER_CLOSED = [0.0]

        # --- Service Clients ---
        self.switch_controller_cli = self.create_client(SwitchController, "/controller_manager/switch_controller")
        self.list_controllers_cli = self.create_client(ListControllers, "/controller_manager/list_controllers")
        
        # --- Publishers ---
        self.arm_pos_publisher = self.create_publisher(JointTrajectory, "/arm_controller/joint_trajectory", 10)
        # self.arm_vel_publisher = self.create_publisher(JointTrajectory, "/arm_velocity_controller/joint_trajectory", 10)
        self.arm_vel_publisher = self.create_publisher(Float64MultiArray, "/arm_velocity_controller/commands", 10)
        self.gripper_publisher = self.create_publisher(JointTrajectory, "/gripper_controller/joint_trajectory", 10)

        # --- Subscriber ---
        self.joint_state_sub = self.create_subscription(JointState, "/joint_states", self.joint_state_callback, 10)
        self.latest_joint_state = None

        self.get_logger().info("Robot Controller CLI started. Waiting for services...")
        self.switch_controller_cli.wait_for_service()
        self.list_controllers_cli.wait_for_service()
        self.get_logger().info("Services are available.")

    def joint_state_callback(self, msg):
        self.latest_joint_state = msg

    def print_menu(self):
        """Prints the main menu of available commands."""
        print("\n" + "="*50)
        print("Robot Control CLI".center(50))
        print("="*50)
        print("\nAvailable Commands:")
        print("  1. Move to Home Position")
        print("  2. Move to Ready Position")
        print("  3. Move to Custom Arm Position")
        print("  4. Open Gripper")
        print("  5. Close Gripper")
        print("  6. Run Velocity Burst (0.5s)")
        print("  7. Show Current Joint Positions")
        print("  8. Switch to Position Control")
        print("  9. Switch to Velocity Control")
        print(" 10. Show Controller Status")
        print("  0. Exit")

    def switch_control_mode(self, activate, deactivate):
        """Switches between controllers."""
        req = SwitchController.Request()
        req.activate_controllers = activate
        req.deactivate_controllers = deactivate
        req.strictness = SwitchController.Request.BEST_EFFORT

        future = self.switch_controller_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        if future.result().ok:
            self.get_logger().info(f"Successfully activated: {activate}")
        else:
            self.get_logger().error(f"Failed to switch controllers.")

    def send_arm_positions(self, positions, duration_sec=2.0):
        """Sends a position command to the arm's trajectory controller."""
        msg = JointTrajectory()
        msg.joint_names = self.ARM_JOINT_NAMES
        point = JointTrajectoryPoint()
        point.positions = [float(p) for p in positions]
        point.time_from_start = Duration(seconds=duration_sec).to_msg()
        msg.points.append(point)
        self.arm_pos_publisher.publish(msg)
        self.get_logger().info(f"Sent position command: {positions}")
        
    def send_gripper_position(self, position):
        """Sends a position command to the gripper's trajectory controller."""
        msg = JointTrajectory()
        msg.joint_names = self.GRIPPER_JOINT_NAME
        point = JointTrajectoryPoint()
        point.positions = [float(p) for p in position]
        point.time_from_start = Duration(seconds=1.0).to_msg()
        msg.points.append(point)
        self.gripper_publisher.publish(msg)
        self.get_logger().info(f"Sent gripper command: {position}")

    def send_arm_velocities(self, velocities):
        """Sends a velocity command to the arm's velocity controller."""
        msg = Float64MultiArray()
        msg.data = [float(v) for v in velocities]
        self.arm_vel_publisher.publish(msg)
        

    def show_joint_positions(self):
        """Prints the current joint positions."""
        if self.latest_joint_state is None:
            self.get_logger().warning("Joint states not yet received.")
            return

        print("\nCurrent Joint Positions (rad):")
        for i, name in enumerate(self.latest_joint_state.name):
            if name in self.ARM_JOINT_NAMES or name in self.GRIPPER_JOINT_NAME:
                 print(f"  {name}: {self.latest_joint_state.position[i]:.3f}")

    def show_controller_status(self):
        """Calls the list_controllers service and prints their status."""
        future = self.list_controllers_cli.call_async(ListControllers.Request())
        rclpy.spin_until_future_complete(self, future)
        
        print("\nController Status:")
        for controller in future.result().controller:
            print(f"  - {controller.name}: {controller.state.upper()} ({controller.type})")

    def run_velocity_burst(self, duration=3.0):
        """Runs the sine wave velocity command for a fixed duration."""
        self.get_logger().info(f"Running velocity burst for {duration} seconds...")
        self.switch_control_mode(activate=["arm_velocity_controller"], deactivate=["arm_controller"])
        
        start_time = self.get_clock().now()
        while rclpy.ok():
            elapsed = (self.get_clock().now() - start_time).nanoseconds / 1e9
            
            # Stop condition
            if elapsed >= duration:
                break
                
            # Calculate and send velocity
            vel = [0.0, 1.5 * math.sin(elapsed * 10), 0.0, -1.5 * math.sin(elapsed * 10), 0.0]
            self.send_arm_velocities(vel)
            time.sleep(0.02) # Loop at ~50Hz

        # Ensure the arm stops
        self.stop_arm()
        self.get_logger().info("Velocity burst finished.")

    def stop_arm(self):
        """Stops any arm motion."""
        self.get_logger().info("Sending stop command to arm...")
        self.send_arm_velocities([0.0] * 5)

    def run(self):
        """Main loop for the CLI."""
        while rclpy.ok():
            self.print_menu()
            try:
                choice = input("Enter command number: ")
            except EOFError:
                break
                
            if choice == "1":
                self.send_arm_positions(self.HOME_POSITION)
            elif choice == "2":
                self.send_arm_positions(self.READY_POSITION)
            elif choice == "3":
                try:
                    pos_str = input("Enter 5 joint positions (rad), comma-separated: ")
                    positions = [float(p) for p in pos_str.split(',')]
                    if len(positions) == 5:
                        self.send_arm_positions(positions)
                    else:
                        print("Invalid input. Please provide 5 numbers.")
                except ValueError:
                    print("Invalid input. Please enter numbers only.")
            elif choice == "4":
                self.send_gripper_position(self.GRIPPER_OPEN)
            elif choice == "5":
                self.send_gripper_position(self.GRIPPER_CLOSED)
            elif choice == "6":
                self.run_velocity_burst()
            elif choice == "7":
                rclpy.spin_once(self, timeout_sec=0.1)
                self.show_joint_positions()
            elif choice == "8":
                self.get_logger().info("Switching to POSITION control...")
                self.switch_control_mode(activate=["arm_controller"], deactivate=["arm_velocity_controller"])
            elif choice == "9":
                self.get_logger().info("Switching to VELOCITY control...")
                self.switch_control_mode(activate=["arm_velocity_controller"], deactivate=["arm_controller"])
            elif choice == "10":
                self.show_controller_status()
            elif choice == "0":
                break
            else:
                print("Invalid choice, please try again.")
            
            time.sleep(0.5)

def main(args=None):
    rclpy.init(args=args)
    cli_node = RobotControllerCLI()
    try:
        cli_node.run()
    except KeyboardInterrupt:
        pass
    finally:
        cli_node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()