#!/bin/bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <inventory-group>  (e.g. remote, raaf)"
    exit 1
fi

exec "$(dirname "$0")/run-test.py" "$1"
