#!/usr/bin/env bash
# ╔═══════════════════════════════════════════════════════════╗
# ║  SHOTER — One-click launcher                             ║
# ║  Automatically sets up venv, installs deps, and runs     ║
# ╚═══════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="venv"
PYTHON=""

# ── Find Python ──────────────────────────────────────────────
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
        major=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
        if [ "$major" -eq 3 ] && [ "$version" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.10+ is required."
    echo "Install it from https://www.python.org/downloads/"
    exit 1
fi

echo "Using: $($PYTHON --version)"

# ── Create venv if needed ────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
fi

# ── Activate and install ─────────────────────────────────────
source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# ── Launch ───────────────────────────────────────────────────
echo ""
echo "  ⚡ Launching SHOTER..."
echo ""
python main.py
