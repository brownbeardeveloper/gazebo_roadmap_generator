#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

ENV_NAME="${ENV_NAME:-gazebo-venv}"
MAP_FILE="${1:-example.yaml}"
WORLD_FILE="${2:-road_play.world}"
CAR_FILE="${CAR_FILE:-sources/car.sdf}"
CMD_TOPIC="${CMD_TOPIC:-/cmd_vel}"
STARTUP_DELAY="${GAZEBO_STARTUP_DELAY:-3}"

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

echo "Building playable world: map=$MAP_FILE car=$CAR_FILE output=$WORLD_FILE"
"${PYTHON[@]}" scripts/build_play_world.py --map "$MAP_FILE" --car "$CAR_FILE" --output "$WORLD_FILE"

export GZ_SIM_RESOURCE_PATH="$PWD${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"

cleanup() {
    gz topic -t "$CMD_TOPIC" -m gz.msgs.Twist -p "linear { x: 0 } angular { z: 0 }" >/dev/null 2>&1 || true
    if [[ -n "${GZ_PID:-}" ]]; then
        kill "$GZ_PID" >/dev/null 2>&1 || true
        wait "$GZ_PID" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT INT TERM

echo "Starting Gazebo Sim..."
gz sim "$WORLD_FILE" &
GZ_PID=$!

sleep "$STARTUP_DELAY"

echo "Drive from this terminal with arrow keys. Press q to quit."
"${PYTHON[@]}" scripts/keyboard_drive.py --topic "$CMD_TOPIC"
