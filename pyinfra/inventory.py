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

mint_vm = [
    (
        "mint_vm",
        {
            "ssh_hostname": "172.16.101.128",
            "ssh_user": _ssh_user,
            "ssh_password": _ssh_and_sudo_password,
            "_sudo_password": _ssh_and_sudo_password,
        }
    )
]

dell_laptop = [
    (
        "dell_laptop",
        {
            "ssh_hostname": "192.168.88.90",
            "ssh_user": _ssh_user,
            "ssh_password": _ssh_and_sudo_password,
            "_sudo_password": _ssh_and_sudo_password,
        }
    )
]
