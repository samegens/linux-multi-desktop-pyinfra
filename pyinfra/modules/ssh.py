"""SSH key + service setup.

Populate as keys are actually needed: add the public key file under files/ssh/<name>.pub,
add a SSH_<NAME>_PRIVATE_KEY constant to secrets_data.py (see desktop-secrets/encrypt.py),
then list <name> in ssh_key_names (group_data/all.py). Empty for now.
"""

from io import BytesIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server

import pkgmgr
import secrets_data
import vault
from services import Service, service_name


@deploy("Configure SSH")
def deploy_ssh():
    username = host.data.username

    pkgmgr.install(name="Install openssh-server", packages=["openssh-server"])

    files.directory(
        name="Create ~/.ssh",
        path=f"/home/{username}/.ssh",
        user=username,
        group=username,
        mode="700",
        _sudo=False,
    )

    for key_name in host.data.ssh_key_names:
        hidden = getattr(secrets_data, f"SSH_{key_name.upper()}_PRIVATE_KEY")
        files.put(
            name=f"Install private key {key_name}",
            src=BytesIO(vault.reveal(hidden)),
            dest=f"/home/{username}/.ssh/{key_name}",
            user=username,
            group=username,
            mode="600",
            _sudo=False,
        )
        files.put(
            name=f"Install public key {key_name}",
            src=f"files/ssh/{key_name}.pub",
            dest=f"/home/{username}/.ssh/{key_name}.pub",
            user=username,
            group=username,
            mode="644",
            _sudo=False,
        )

    server.service(
        name="Enable ssh service",
        service=service_name(Service.SSH),
        running=True,
        enabled=True,
    )


deploy_ssh()
