#!/usr/bin/env bash
set -euo pipefail

if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  exec claude --name "$(basename "$PWD")" --ide
else
  exec claude
fi
