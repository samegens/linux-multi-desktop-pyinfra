"""pyinfra inventory

Groups double as --limit targets, e.g.:
    pyinfra inventory.py deploy.py --limit localhost
"""

import secrets_data
import vault

localhost = ["@local"]

raaf = [
    ("raaf", {"ssh_hostname": "192.168.88.155", "ssh_user": "sebastiaan"}),
]

# Not a fixed machine - a generic placeholder host used when configuring some new/different
# desktop machine from the current one. Currently pointed at the Mint test VM.
_remote_password = vault.reveal(secrets_data.SSH_PASSWORD).decode()

remote = [
    (
        "remote",
        {
            "ssh_hostname": "192.168.149.134",
            "ssh_user": "sebastiaan",
            "ssh_password": _remote_password,
            # Underscore-prefixed to match pyinfra's global argument name exactly -
            # that's how host data overrides it (see pyinfra.api.arguments.pop_global_arguments).
            "_sudo_password": _remote_password,
        },
    ),
]
