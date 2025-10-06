#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT_DIR/.venv"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Python venv not found at $VENV. Creating and installing deps..."
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade pip
  "$VENV/bin/pip" install -r "$ROOT_DIR/requirements.txt"
fi

exec "$VENV/bin/python" "$ROOT_DIR/scripts/flight_scraper_12306.py" "$@"


