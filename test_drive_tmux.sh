#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

SESSION="${TMUX_SESSION:-roadmap_drive_test}"
MAP_FILE="${1:-example.yaml}"
WORLD_FILE="${2:-road_play.world}"
CMD_TOPIC="${CMD_TOPIC:-/cmd_vel}"
ODOM_TOPIC="${ODOM_TOPIC:-/model/roadmap_car/odometry}"
ROS_SETUP="${ROS_SETUP:-}"

if ! command -v tmux >/dev/null 2>&1; then
    echo "tmux not found. Install it with: sudo apt install tmux"
    exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Attaching existing tmux session: $SESSION"
    exec tmux attach-session -t "$SESSION"
fi

if [[ -z "$ROS_SETUP" ]]; then
    if [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/$ROS_DISTRO/setup.bash" ]]; then
        ROS_SETUP="/opt/ros/$ROS_DISTRO/setup.bash"
    elif [[ -f "/opt/ros/jazzy/setup.bash" ]]; then
        ROS_SETUP="/opt/ros/jazzy/setup.bash"
    elif [[ -f "/opt/ros/humble/setup.bash" ]]; then
        ROS_SETUP="/opt/ros/humble/setup.bash"
    else
        echo "Could not find ROS 2 setup.bash. Set ROS_SETUP=/opt/ros/<distro>/setup.bash"
        exit 1
    fi
fi

if [[ ! -f "$ROS_SETUP" ]]; then
    echo "ROS setup file not found: $ROS_SETUP"
    exit 1
fi

ros_cmd() {
    local setup
    printf -v setup '%q' "$ROS_SETUP"
    printf 'bash -lc %q' "source $setup && $1"
}

tmux new-session -d -s "$SESSION" -n gazebo \
    "$(ros_cmd "KEYBOARD_DRIVE=off ./play.sh '$MAP_FILE' '$WORLD_FILE'")"

tmux split-window -h -t "$SESSION:0" \
    "$(ros_cmd "sleep 6; echo 'Watching odometry: $ODOM_TOPIC'; ros2 topic echo '$ODOM_TOPIC'")"

tmux split-window -v -t "$SESSION:0.1" \
    "$(ros_cmd "sleep 6; echo 'Press Enter to publish forward /cmd_vel. Press Ctrl+C to stop.'; read; ros2 topic pub --rate 20 '$CMD_TOPIC' geometry_msgs/msg/Twist '{linear: {x: 0.8}, angular: {z: 0.0}}'")"

tmux split-window -v -t "$SESSION:0.0" \
    "$(ros_cmd "sleep 6; echo 'Gazebo topics:'; gz topic -l | grep roadmap_car || true; echo; echo 'ROS topics:'; ros2 topic list | grep -E 'cmd_vel|roadmap_car' || true; echo; echo 'This pane is only diagnostics. Press Ctrl+C in the publisher pane to stop the test command.'; bash")"

tmux select-layout -t "$SESSION:0" tiled
tmux select-pane -t "$SESSION:0.2"
tmux attach-session -t "$SESSION"
