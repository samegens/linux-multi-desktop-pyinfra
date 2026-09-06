"""SSH key + service setup.

Add new keys: add the public key file under files/ssh/<name>.pub,
add a SSH_<NAME>_PRIVATE_KEY constant to secrets_data.py (see desktop-secrets/encrypt.py) - hyphens
in <name> become underscores in the constant name - then list <name> in ssh_key_names
(group_data/all.py).

SSH_CONFIG_TEMPLATE's Host aliases for internet-reachable personal servers (backup_server,
public_vps, website_server, public_home_server) are deliberately generic - their real
HostName/User/Port live in secrets_data.py, not this file.

The "desktop" key is deliberately shared across every one of this repo's own desktop/laptop
machines (framework16, dell_laptop, raaf) for mutual passwordless SSH between them, unlike
every other key here which is scoped to one external destination. That's a deliberate exception,
not an oversight: these three machines already share one vault password via Dropbox,
so a compromise of any one already exposes every secret in
secrets_data.py regardless. It's
used both ways: install_user_keys() below deploys it like any other outbound key, and
install_authorized_keys() additionally authorizes its public half for INBOUND login - the only
key here that needs that, since every other key only ever connects out.
"""

from io import BytesIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files, server

import pkgmgr
import secrets_data
import vault
from services import Service, get_service_name

ROOT_SSH_KEY_NAMES = ["fitlet", "cubi", "fitlet-tst", "fitlet-acc", "liteserver", "liteserver-tst"]

SSH_CONFIG_TEMPLATE = """Host fitlet
    IdentityFile ~/.ssh/fitlet

Host fitpc
    HostName {fitpc_fqdn}
    IdentityFile ~/.ssh/fitpc
    Port {fitpc_port}

Host backup_server
    HostName {backup_server_hostname}
    IdentityFile ~/.ssh/fitpc
    Port {backup_server_port}

Host liteserver
    HostName {public_vps_hostname}
    User {public_vps_user}
    IdentityFile ~/.ssh/liteserver
    Port {public_vps_port}

Host cubi
    IdentityFile ~/.ssh/cubi

Host homeserver
    IdentityFile ~/.ssh/homeserver

Host bhosted
    HostName {website_server_hostname}
    User {website_server_user}
    IdentityFile ~/.ssh/bhosted
    Port {website_server_port}

# Desktop/laptop machines - mutual passwordless SSH via the shared "desktop" key (see this
# module's docstring for why sharing one key across just these three is a deliberate exception).
# Static LAN IPs, like every other Host block here - check pyinfra/inventory.py if one changes.
Host fluitzwaan
    HostName 192.168.88.103
    IdentityFile ~/.ssh/desktop

Host dwerglijster
    HostName 192.168.88.90
    IdentityFile ~/.ssh/desktop

Host raaf
    HostName 192.168.88.155
    IdentityFile ~/.ssh/desktop

# GitHub Account samegens
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_samegens

# Bitbucket Account ongoonku
Host bitbucket.org
    HostName bitbucket.org
    User git
    IdentityFile ~/.ssh/github_samegens

# GitHub Account blauwe-lucht
Host github.com-blauwe-lucht
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_blauwe-lucht

Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/gitlab

Host github_adopteerregenwoud
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_adopteerregenwoud

Host thuis
    HostName {public_home_server_hostname}
    User {public_home_server_user}
    IdentityFile ~/.ssh/homeserver
    Port {public_home_server_port}
    LocalForward 8096 localhost:8096
    ServerAliveInterval 60

# Entry for new machine that needs to be configured using pyinfra.
Host new-machine
    HostName 192.168.88.181
    PreferredAuthentications password
    PubkeyAuthentication no
"""

def reveal_private_key(key_name: str) -> bytes:
    attr_name = f"SSH_{key_name.upper().replace('-', '_')}_PRIVATE_KEY"
    hidden = getattr(secrets_data, attr_name)
    return vault.reveal(hidden)

def install_user_keys(username: str):
    for key_name in host.data.ssh_key_names:
        files.put(
            name=f"Install private key {key_name}",
            src=BytesIO(reveal_private_key(key_name)),
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

    files.link(
        name="Create homeserver private key symlink (uses cubi key)",
        path=f"/home/{username}/.ssh/homeserver",
        target=f"/home/{username}/.ssh/cubi",
        user=username,
        group=username,
    )
    files.link(
        name="Create homeserver public key symlink (uses cubi key)",
        path=f"/home/{username}/.ssh/homeserver.pub",
        target=f"/home/{username}/.ssh/cubi.pub",
        user=username,
        group=username,
    )

def install_ssh_config(username: str):
    config = SSH_CONFIG_TEMPLATE.format(
        fitpc_port=vault.reveal(secrets_data.SSH_FITPC_PORT).decode(),
        fitpc_fqdn=vault.reveal(secrets_data.SSH_FITPC_FQDN).decode(),
        backup_server_hostname=vault.reveal(secrets_data.SSH_BACKUP_SERVER_HOSTNAME).decode(),
        backup_server_port=vault.reveal(secrets_data.SSH_BACKUP_SERVER_PORT).decode(),
        public_vps_hostname=vault.reveal(secrets_data.SSH_PUBLIC_VPS_HOSTNAME).decode(),
        public_vps_user=vault.reveal(secrets_data.SSH_PUBLIC_VPS_USER).decode(),
        public_vps_port=vault.reveal(secrets_data.SSH_PUBLIC_VPS_PORT).decode(),
        website_server_hostname=vault.reveal(secrets_data.SSH_WEBSITE_SERVER_HOSTNAME).decode(),
        website_server_user=vault.reveal(secrets_data.SSH_WEBSITE_SERVER_USER).decode(),
        website_server_port=vault.reveal(secrets_data.SSH_WEBSITE_SERVER_PORT).decode(),
        public_home_server_hostname=vault.reveal(
            secrets_data.SSH_PUBLIC_HOME_SERVER_HOSTNAME
        ).decode(),
        public_home_server_user=vault.reveal(secrets_data.SSH_PUBLIC_HOME_SERVER_USER).decode(),
        public_home_server_port=vault.reveal(secrets_data.SSH_PUBLIC_HOME_SERVER_PORT).decode(),
    )
    files.put(
        name="Install ~/.ssh/config",
        src=BytesIO(config.encode()),
        dest=f"/home/{username}/.ssh/config",
        user=username,
        group=username,
        mode="600",
        _sudo=False,
    )

AUTHORIZED_PUBLIC_KEY_NAMES = ["desktop"]

def install_authorized_keys(username: str):
    """Authorizes the public half of each key in AUTHORIZED_PUBLIC_KEY_NAMES for inbound login -
    every other key in this file only ever connects out, so this is the one place that manages
    authorized_keys at all."""
    ssh_dir = f"/home/{username}/.ssh"
    authorized_keys_path = f"{ssh_dir}/authorized_keys"
    files.file(
        name="Create ~/.ssh/authorized_keys",
        path=authorized_keys_path,
        user=username,
        group=username,
        mode="600",
        _sudo=False,
    )
    for key_name in AUTHORIZED_PUBLIC_KEY_NAMES:
        with open(f"files/ssh/{key_name}.pub") as f:
            public_key = f.read().strip()
        files.line(
            name=f"Authorize {key_name} public key for inbound SSH",
            path=authorized_keys_path,
            line=public_key,
            escape_regex_characters=True,
            extended_regex=True,
            _sudo=False,
        )

def install_root_keys():
    files.directory(
        name="Create /root/.ssh",
        path="/root/.ssh",
        mode="700",
    )

    for key_name in ROOT_SSH_KEY_NAMES:
        files.put(
            name=f"Install root private key {key_name}",
            src=BytesIO(reveal_private_key(key_name)),
            dest=f"/root/.ssh/{key_name}",
            mode="700",
        )

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

    install_user_keys(username)
    install_ssh_config(username)
    install_authorized_keys(username)
    install_root_keys()

    server.service(
        name="Enable ssh service",
        service=get_service_name(Service.SSH),
        running=True,
        enabled=True,
    )

deploy_ssh()
