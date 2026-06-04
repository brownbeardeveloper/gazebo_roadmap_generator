#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

mkdir -p "$HOME/.gazebo/models"
uv sync
uv run python wizard.py "$@"
