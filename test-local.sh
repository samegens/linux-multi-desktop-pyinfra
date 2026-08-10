#!/bin/bash
set -euo pipefail

exec "$(dirname "$0")/_run-test.py" localhost "$@"
