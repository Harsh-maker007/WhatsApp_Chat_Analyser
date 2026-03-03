#!/usr/bin/env bash
set -euo pipefail

# Pick an available Python executable.
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python is not installed or not on PATH."
  exit 1
fi

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

# Activate environment
source .venv/bin/activate

# Upgrade packaging tools
python -m pip install --upgrade pip setuptools wheel

# Install app dependencies (use requirements.txt if present).
if [ -f "requirements.txt" ]; then
  python -m pip install -r requirements.txt
else
  python -m pip install streamlit pandas
fi

echo
echo "Setup complete."
echo "Run the app with:"
echo "  streamlit run app.py"
