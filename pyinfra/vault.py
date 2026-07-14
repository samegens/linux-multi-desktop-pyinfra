"""Decrypts secrets_data.py values, encrypted with privy.

Not named secrets.py on purpose: that would shadow the stdlib secrets module for
anything importing from this directory.
"""

import os
from pathlib import Path

import privy

VAULT_PASSWORD_ENV_VAR = "VAULT_PASSWORD"

# Shared with fedora-desktop's vault-client.sh - don't fork this into a second password file.
VAULT_PASSWORD_FILE = Path("~/Dropbox/ansible/.vault_pass").expanduser()


def vault_password() -> str:
    if password := os.environ.get(VAULT_PASSWORD_ENV_VAR):
        return password
    if VAULT_PASSWORD_FILE.exists():
        return VAULT_PASSWORD_FILE.read_text().strip()
    raise RuntimeError(
        f"{VAULT_PASSWORD_ENV_VAR} not set and {VAULT_PASSWORD_FILE} not found"
    )


def reveal(hidden: str) -> bytes:
    """Decrypt a privy.hide() token from secrets_data.py."""
    return privy.peek(hidden, vault_password())
