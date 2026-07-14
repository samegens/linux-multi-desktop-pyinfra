#!/bin/bash
# Repository setup script
# Symlinks pyinfra/secrets_data.py from the sibling desktop-secrets directory.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_DIR="$(cd "$REPO_DIR/../desktop-secrets" 2>/dev/null && pwd)" || {
  echo "Error: desktop-secrets directory not found at $REPO_DIR/../desktop-secrets"
  echo "Make sure the secrets directory exists and Dropbox is synced before running this script."
  exit 1
}

echo "Setting up repository..."
echo "Secrets directory: $SECRETS_DIR"
echo ""

create_symlink() {
  local target="$1"
  local link="$2"
  if [ -L "$link" ]; then
    echo "  (already exists) $link"
  elif [ -e "$link" ]; then
    echo "  WARNING: $link exists and is not a symlink, skipping"
  else
    ln -s "$target" "$link"
    echo "  ✓ $link"
  fi
}

echo "Creating symlinks to secrets..."

create_symlink "$SECRETS_DIR/secrets_data.py" \
               "$REPO_DIR/pyinfra/secrets_data.py"

echo ""
echo "Repository setup complete!"
