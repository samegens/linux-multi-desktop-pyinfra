#!/bin/bash
# Bootstraps pyinfra itself on a fresh box before the deploy can run.

set -euo pipefail

if [ "$EUID" -eq 0 ]; then
    echo "Please run as your normal user, not root (this script uses sudo where needed)"
    exit 1
fi

sudo apt-get update
sudo apt-get install -y python3-venv python3-pip

VENV_DIR="$HOME/python3-venv/pyinfra-latest"
if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
    echo "Creating pyinfra venv at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing pyinfra + privy into $VENV_DIR..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$(dirname "${BASH_SOURCE[0]}")/requirements.txt"

echo
echo "Done. Then:"
echo "  ./setup-repo.sh"
echo "  cd pyinfra && ./run-local.sh"
