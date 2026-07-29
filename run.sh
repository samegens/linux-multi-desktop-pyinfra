#!/bin/bash
# Runs pyinfra against an inventory group, tee-ing output to a timestamped log.
#
# Usage: ./run.sh <host> [modules...] [pyinfra options...]
#   Bare module names are resolved to modules/<name>.py; with no modules given, deploy.py
#   is run instead.
#   e.g. ./run.sh mint_vm -y                  # deploy.py
#        ./run.sh mint_vm base ssh -y         # modules/base.py modules/ssh.py
#        ./run.sh dell_laptop modules/git.py

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

list_modules() {
    find "$REPO_DIR/pyinfra/modules" -maxdepth 1 -name '*.py' \
        ! -name '__init__.py' -exec basename {} .py \; | sort | tr '\n' ' '
}

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <host> [modules...] [pyinfra options...]"
    echo ""
    echo "Hosts: localhost, mint_vm, dell_laptop, raaf"
    echo "Modules: $(list_modules)" | fold -s -w 80
    exit 1
fi

host="$1"
shift

targets=()
options=()
for arg in "$@"; do
    case "$arg" in
        -*)
            options+=("$arg")
            ;;
        *.py)
            targets+=("$arg")
            ;;
        *)
            targets+=("modules/$arg.py")
            ;;
    esac
done

if [ "${#targets[@]}" -eq 0 ]; then
    targets=(deploy.py)
fi

PYINFRA="$HOME/python3-venv/pyinfra-latest/bin/pyinfra"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-$host.log"

mkdir -p "$LOG_DIR"
echo "Logging to $LOG_FILE"

cd "$REPO_DIR/pyinfra"
"$PYINFRA" inventory.py "${targets[@]}" --limit "$host" "${options[@]}" -v 2>&1 | tee "$LOG_FILE"
