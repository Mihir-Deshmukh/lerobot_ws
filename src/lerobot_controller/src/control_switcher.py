#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from controller_manager_msgs.srv import SwitchController
import argparse
import sys


class ControlSwitcher(Node):
    def __init__(self):
        super().__init__("control_switcher")
        self.cli = self.create_client(SwitchController, "/controller_manager/switch_controller")
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("service not available, waiting again...")

    def switch(self, activate_controllers, deactivate_controllers):
        req = SwitchController.Request()
        req.activate_controllers = activate_controllers
        req.deactivate_controllers = deactivate_controllers
        req.strictness = SwitchController.Request.BEST_EFFORT
        req.activate_asap = False
        req.timeout = rclpy.duration.Duration(seconds=5.0).to_msg()

        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None:
            if future.result().ok:
                self.get_logger().info("Successfully switched controllers")
            else:
                self.get_logger().error("Failed to switch controllers")
        else:
            self.get_logger().error("Exception while calling service: %r" % future.exception())


def main(args=None):
    rclpy.init(args=args)
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["position", "velocity"], help="Control mode to switch to")
    parsed_args = parser.parse_args(sys.argv[1:])

    switcher = ControlSwitcher()
    if parsed_args.mode == "position":
        switcher.switch(["arm_controller"], ["arm_velocity_controller"])
    else:
        switcher.switch(["arm_velocity_controller"], ["arm_controller"])

    switcher.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()