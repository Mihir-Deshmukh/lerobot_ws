# ROS2 Robotic Arm Control

## Challenge Implementation Overview

This version addresses the requirements by adding comprehensive control interfaces and depth camera integration to the existing SO-ARM101 packages.

### Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Basic Control** | ✅ Complete | Added CLI interface + position/velocity control switching |
| **Depth Camera Integration** | ✅ Complete | RGB + Depth + Point Cloud publishing in Gazebo |

---

## Quick Start

### Prerequisites
- ROS2 Jazzy Jalisco
- Gazebo Harmonic
- All dependencies from original repository

### Installation
```bash
# Clone the enhanced repository
git clone https://github.com/Mihir-Deshmukh/lerobot_ws.git
cd lerobot_ws

# Install additional dependencies for enhancements
sudo apt install ros-jazzy-ros-gz-bridge ros-jazzy-joint-trajectory-controller ros-jazzy-velocity-controllers

# Build with symlink for development
colcon build --symlink-install
source install/setup.bash
```

### One-Command Launch (NEW)
```bash
# Launch everything: Gazebo + Controllers + MoveIt + Camera feeds
ros2 launch lerobot_bringup lerobot_bringup.launch.py
```

### Interactive Robot Control (NEW)
```bash
# Run the enhanced CLI interface
ros2 run lerobot_controller robot_cli.py
```

---

## What's New

### 1. **Orchestration Package** (`lerobot_bringup`) - NEW
- **Single command launch** for complete system
- **Timed initialization** (Gazebo → Controllers → MoveIt)
- **Integrated camera feeds** with proper transforms

### 2. **Enhanced Controller Package** (`lerobot_controller`) - EXTENDED
- **Interactive CLI interface** for real-time control
- **Dual control modes**: Position <-> Velocity switching
- **Pre-defined poses**: Home, Ready positions
- **Velocity demonstrations**: Sine wave motion patterns

### 3. **Depth Camera Integration** - NEW
- **RGB Camera**: `/camera` topic with calibration info
- **Depth Camera**: `/camera_depth` with proper data types  
- **Point Cloud**: `/depth_camera/points` for 3D perception
- **Gazebo Bridge**: Custom configuration for Harmonic compatibility

---

## Enhanced Control Interface

The new CLI provides intuitive robot control:

```bash
Robot Control CLI
==========================================
Available Commands:
  1. Move to Home Position      # All joints -> 0°
  2. Move to Ready Position     # Pre-defined manipulation pose
  3. Move to Custom Position    # User-defined joint angles
  4. Open Gripper              # Gripper control
  5. Close Gripper             
  6. Run Velocity Burst        # Sine wave demo (3 seconds)
  7. Show Current Positions    # Real-time joint feedback
  8. Switch to Position Mode   # Controller switching
  9. Switch to Velocity Mode   
 10. Show Controller Status    # System diagnostics
  0. Exit
```

---

### Updated Structure
```
src/
├── lerobot_bringup/            # ADDED: System orchestration
│   └── launch/
│       └── lerobot_bringup.launch.py
├── lerobot_controller/         # ADDED: Advanced control
│   ├── config/
│   │   └── so101_controllers.yaml    # Updated for dual-mode
│   ├── launch/
│   │   └── so101_controller.launch.py
│   └── src/
│       ├── robot_cli.py              # Interactive CLI
│       └── control_switcher.py       # Controller management
├── lerobot_description/        # ADDED: Camera integration
│   ├── urdf/                         # Extended with depth camera
│   └── launch/
│       └── so101_gazebo.launch.py    # Enhanced bridge config
└── lerobot_moveit/            # ADDED: Launch compatibility
    └── launch/
        └── so101_moveit.launch.py    # Fixed xacro compatibility
```

---

## Terminal Commands (Alternative to the CLI)

### Controller Switching
```bash
# Runtime switching between control modes
ros2 service call /controller_manager/switch_controller \
  controller_manager_msgs/SwitchController \
  "{activate_controllers: ['arm_velocity_controller'], 
    deactivate_controllers: ['arm_controller']}"
```

### Direct Joint Control
```bash
# Position commands
ros2 topic pub /arm_controller/joint_trajectory trajectory_msgs/JointTrajectory \
  "{joint_names: ['1','2','3','4','5'], 
    points: [{positions: [0.0, -0.5, 1.0, -1.5, 0.0], 
             time_from_start: {sec: 2}}]}" --once

# Velocity commands (after switching to velocity mode)
ros2 topic pub /arm_velocity_controller/commands std_msgs/Float64MultiArray \
  "{data: [0.1, 0.2, 0.0, -0.1, 0.0]}" --once
```

---

**Repository**: https://github.com/Mihir-Deshmukh/lerobot_ws  
**Branch**: `bench/ros2-arm101`