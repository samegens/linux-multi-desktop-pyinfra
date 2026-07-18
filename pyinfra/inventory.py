"""pyinfra inventory

Groups double as --limit targets, e.g.:
    pyinfra inventory.py deploy.py --limit localhost
"""

import secrets_data
import vault

_ssh_user = "sebastiaan"
_ssh_and_sudo_password = vault.reveal(secrets_data.SSH_PASSWORD).decode()

localhost = [
    (
        "@local",
        {
            "_sudo_password": _ssh_and_sudo_password
        }
    )
]

raaf = [
    (
        "raaf",
        {
            "ssh_hostname": "192.168.88.155",
            "ssh_user": _ssh_user,
            "ssh_password": _ssh_and_sudo_password,
            "_sudo_password": _ssh_and_sudo_password,
        }
    )
]

# Not a fixed machine - a generic placeholder host used when configuring some new/different
# desktop machine from the current one. Currently pointed at the Mint test VM.

remote = [
    (
        "remote",
        {
            "ssh_hostname": "192.168.149.134",
            "ssh_user": _ssh_user,
            "ssh_password": _ssh_and_sudo_password,
            "_sudo_password": _ssh_and_sudo_password,
        }
    )
]
