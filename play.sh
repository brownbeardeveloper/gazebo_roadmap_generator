#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

ENV_NAME="${ENV_NAME:-gazebo-venv}"
MAP_FILE="${1:-example.yaml}"
WORLD_FILE="${2:-road_play.world}"
CAR_FILE="${CAR_FILE:-sources/car.sdf}"
CMD_TOPIC="${CMD_TOPIC:-/cmd_vel}"
CAMERA_IMAGE_TOPIC="${CAMERA_IMAGE_TOPIC:-/model/roadmap_car/front_camera/image}"
CAMERA_INFO_TOPIC="${CAMERA_INFO_TOPIC:-/model/roadmap_car/front_camera/camera_info}"
STARTUP_DELAY="${GAZEBO_STARTUP_DELAY:-3}"
ROS_BRIDGE="${ROS_BRIDGE:-auto}"
BRIDGE_CONFIG="${BRIDGE_CONFIG:-config/ros_gz_bridge.yaml}"

if ! command -v micromamba >/dev/null 2>&1; then
    echo "micromamba not found in PATH. Install micromamba or create the Python environment manually."
    exit 1
fi

if ! micromamba --version >/dev/null 2>&1; then
    echo "micromamba is installed but failed to start. Please fix the micromamba installation."
    exit 1
fi

if ! micromamba env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
    micromamba env create -f environment.yml
fi

if ! command -v gz >/dev/null 2>&1; then
    echo "gz not found in PATH. Run this inside the Linux VM with Gazebo Sim installed."
    exit 1
fi

PYTHON=(micromamba run -n "$ENV_NAME" python)
DRIVE_PYTHON=("${PYTHON[@]}")
DRIVE_TRANSPORT="gz"

if command -v python3 >/dev/null 2>&1 && python3 -c "import rclpy, geometry_msgs.msg" >/dev/null 2>&1; then
    DRIVE_PYTHON=(python3)
    DRIVE_TRANSPORT="ros2"
fi

start_ros_bridge() {
    if [[ "$ROS_BRIDGE" == "off" ]]; then
        return
    fi

    if ! command -v ros2 >/dev/null 2>&1; then
        echo "ROS 2 not found in PATH; driving with Gazebo Transport only."
        return
    fi

    if ! ros2 pkg prefix ros_gz_bridge >/dev/null 2>&1; then
        echo "ros_gz_bridge not found; /cmd_vel will not appear in ros2 topic list."
        echo "Install it in the VM, for example: sudo apt install ros-\$ROS_DISTRO-ros-gz-bridge"
        return
    fi

    echo "Starting ROS 2 bridge from $BRIDGE_CONFIG..."
    ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:="$BRIDGE_CONFIG" &
    BRIDGE_PID=$!
}

echo "Building playable world: map=$MAP_FILE car=$CAR_FILE output=$WORLD_FILE"
"${PYTHON[@]}" scripts/build_play_world.py --map "$MAP_FILE" --car "$CAR_FILE" --output "$WORLD_FILE"

export GZ_SIM_RESOURCE_PATH="$PWD${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"

cleanup() {
    gz topic -t "$CMD_TOPIC" -m gz.msgs.Twist -p "linear { x: 0 } angular { z: 0 }" >/dev/null 2>&1 || true
    if [[ -n "${BRIDGE_PID:-}" ]]; then
        kill "$BRIDGE_PID" >/dev/null 2>&1 || true
        wait "$BRIDGE_PID" >/dev/null 2>&1 || true
    fi
    if [[ -n "${GZ_PID:-}" ]]; then
        kill "$GZ_PID" >/dev/null 2>&1 || true
        wait "$GZ_PID" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT INT TERM

echo "Starting Gazebo Sim..."
gz sim -r "$WORLD_FILE" &
GZ_PID=$!

sleep "$STARTUP_DELAY"
start_ros_bridge

echo "Drive from this terminal with arrow keys. Press q to quit."
"${DRIVE_PYTHON[@]}" scripts/keyboard_drive.py --topic "$CMD_TOPIC" --transport "$DRIVE_TRANSPORT"
