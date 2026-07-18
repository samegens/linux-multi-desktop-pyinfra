#!/bin/bash
# Runs everything CI runs. Used directly by .github/workflows/ci.yml and meant to be run
# locally before pushing - single source of truth for both.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-$HOME/python3-venv/pyinfra-latest/bin/python3}"
# Resolve to an absolute path - pyright's --pythonpath needs a real file path, not a bare
# command name. $PYTHON is always absolute when the default above is used, but CI overrides
# it to the bare command "python3", which pyright can't resolve on its own.
PYTHON="$(command -v "$PYTHON")"

echo "==> pyright (pyinfra/)"
"$PYTHON" -m pip install -q pyright
"$PYTHON" -m pyright --pythonpath "$PYTHON" pyinfra/

echo "==> unit tests (pyinfra/tests)"
(cd pyinfra && "$PYTHON" -m unittest discover -s tests -p 'test_*.py')

echo "==> inspec profile check (inspec/mint-desktop)"
cinc-auditor check inspec/mint-desktop --chef-license=accept-silent

echo "==> all checks passed"
