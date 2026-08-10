#!/bin/bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <inventory-group> [tag]  (e.g. mint_vm, dell_laptop, raaf; optional tag e.g. tools)"
    exit 1
fi

exec "$(dirname "$0")/_run-test.py" "$@"
