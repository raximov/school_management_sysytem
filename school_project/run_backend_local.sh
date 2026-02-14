#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

VENV_PATH="../venv"
if [ ! -d "$VENV_PATH" ]; then
  echo "venv folder not found at $VENV_PATH"
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_PATH/bin/activate"
python3 manage.py runserver 0.0.0.0:8000
