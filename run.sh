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

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <host> [modules...] [pyinfra options...]  (e.g. localhost, mint_vm, dell_laptop, raaf)"
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

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYINFRA="$HOME/python3-venv/pyinfra-latest/bin/pyinfra"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-$host.log"

mkdir -p "$LOG_DIR"
echo "Logging to $LOG_FILE"

cd "$REPO_DIR/pyinfra"
"$PYINFRA" inventory.py "${targets[@]}" --limit "$host" "${options[@]}" 2>&1 | tee "$LOG_FILE"
