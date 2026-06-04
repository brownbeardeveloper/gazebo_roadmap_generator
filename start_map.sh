#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

ENV_NAME="gazebo-venv"

if ! command -v micromamba >/dev/null 2>&1; then
    echo "micromamba not found in PATH. Install micromamba or run python wizard.py directly."
    exit 1
fi

if ! micromamba --version >/dev/null 2>&1; then
    echo "micromamba is installed but failed to start. Please fix the micromamba installation."
    exit 1
fi

if ! micromamba env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
    micromamba env create -f environment.yml
fi

micromamba run -n "$ENV_NAME" python wizard.py "$@"
