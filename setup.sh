#!/usr/bin/env bash
# setup.sh - Install all project dependencies (macOS / Linux)
#
# Usage:
#   ./setup.sh              Install Python + Flutter dependencies
#   ./setup.sh --python     Install Python dependencies only
#   ./setup.sh --flutter    Install Flutter dependencies only
#
# Creates a Python virtual environment in .venv and installs requirements.txt,
# then runs `flutter pub get` for the mobile app.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLUTTER_DIR="$REPO_ROOT/app/final_design"
VENV_DIR="$REPO_ROOT/.venv"

DO_PYTHON=false
DO_FLUTTER=false
case "${1:-}" in
    --python)  DO_PYTHON=true ;;
    --flutter) DO_FLUTTER=true ;;
    "")        DO_PYTHON=true; DO_FLUTTER=true ;;
    *) echo "Unknown option: $1"; echo "Use --python, --flutter, or no argument."; exit 1 ;;
esac

# Colors (fall back to plain if not a terminal)
if [ -t 1 ]; then
    C_CYAN='\033[0;36m'; C_GREEN='\033[0;32m'; C_YELLOW='\033[0;33m'; C_RESET='\033[0m'
else
    C_CYAN=''; C_GREEN=''; C_YELLOW=''; C_RESET=''
fi
step() { printf "\n${C_CYAN}==> %s${C_RESET}\n" "$1"; }
ok()   { printf "    ${C_GREEN}[ok] %s${C_RESET}\n" "$1"; }
warn() { printf "    ${C_YELLOW}[!]  %s${C_RESET}\n" "$1"; }

install_python() {
    step "Python backend + ML dependencies"

    PY=""
    for cand in python3 python; do
        if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
    done
    if [ -z "$PY" ]; then
        echo "Python not found. Install Python 3.10+ from https://python.org and re-run." >&2
        exit 1
    fi
    ok "Using interpreter: $PY"

    if [ ! -d "$VENV_DIR" ]; then
        echo "    Creating virtual environment in .venv ..."
        "$PY" -m venv "$VENV_DIR"
    else
        ok "Virtual environment .venv already exists"
    fi

    VENV_PY="$VENV_DIR/bin/python"
    echo "    Upgrading pip ..."
    "$VENV_PY" -m pip install --upgrade pip --quiet
    echo "    Installing requirements.txt ..."
    "$VENV_PY" -m pip install -r "$REPO_ROOT/requirements.txt"
    ok "Python dependencies installed"
    echo "    Activate with: source .venv/bin/activate"
}

install_flutter() {
    step "Flutter app dependencies"

    if ! command -v flutter >/dev/null 2>&1; then
        warn "Flutter SDK not found. Skipping Flutter dependencies."
        warn "Install Flutter 3.x from https://docs.flutter.dev/get-started/install"
        return
    fi
    if [ ! -d "$FLUTTER_DIR" ]; then
        warn "Flutter project not found at $FLUTTER_DIR. Skipping."
        return
    fi

    ( cd "$FLUTTER_DIR" && echo "    Running flutter pub get ..." && flutter pub get )
    ok "Flutter dependencies installed"
}

$DO_PYTHON  && install_python
$DO_FLUTTER && install_flutter

printf "\n${C_GREEN}Done.${C_RESET}\n"
