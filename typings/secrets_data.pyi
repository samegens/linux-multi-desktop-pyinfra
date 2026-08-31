"""
Type stub for secrets_data - the real file is a gitignored symlink into ../desktop-secrets
(see setup-repo.sh), so it doesn't exist in a fresh checkout (e.g. CI). Declares only the
constants actually referenced by name elsewhere in this repo - SSH_<NAME>_PRIVATE_KEY keys
are accessed dynamically via getattr() in modules/ssh.py, so they need no stub entry.
"""

SSH_PASSWORD: str
SSH_FITPC_PORT: str
SSH_FITPC_FQDN: str
SSH_BACKUP_SERVER_HOSTNAME: str
SSH_BACKUP_SERVER_PORT: str
SSH_PUBLIC_VPS_HOSTNAME: str
SSH_PUBLIC_VPS_USER: str
SSH_PUBLIC_VPS_PORT: str
SSH_WEBSITE_SERVER_HOSTNAME: str
SSH_WEBSITE_SERVER_USER: str
SSH_WEBSITE_SERVER_PORT: str
SSH_PUBLIC_HOME_SERVER_HOSTNAME: str
SSH_PUBLIC_HOME_SERVER_USER: str
SSH_PUBLIC_HOME_SERVER_PORT: str
