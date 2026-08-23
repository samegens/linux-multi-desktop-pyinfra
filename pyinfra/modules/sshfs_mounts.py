"""SSHFS mounts. This SSHFS mount reaches the full /data
tree (including root-only/private subdirs like _backup) of homeserver
gated by SSH key auth as a specific remote user.

The client package name differs by manager - not a distro property, a naming one
(Fedora's fuse-sshfs vs Debian/Ubuntu's sshfs). Handled via
PACKAGE_NAME_OVERRIDES like any other apt/dnf name divergence.

The mount happens as root (systemd's fstab-generated .mount unit, same as any other fstab
entry), not as the login user - so root's own known_hosts needs the server's SSH host key, and the
IdentityFile mount option must be an absolute path, not "~" - that would expand to /root, which
doesn't have the login user's key.

The initial mount is done via a manual is-mounted check + server.shell, not server.mount(mounted=
True, options=[...]) - confirmed live (mint_vm) that omitting options entirely makes the bare
`mount -t fuse.sshfs` fall back to default/interactive auth and the connection gets reset.
But passing them to server.mount's own options=
breaks idempotency the same way nfs_mounts.py's _netdev did: none of IdentityFile=/uid=/gid=/
ServerAliveInterval=/reconnect show up in the live kernel-reported mount options table (only
allow_other and the generic rw/nosuid/etc. flags do), so server.mount's `set(options) -
set(mounted_options)` would always find them "missing" and remount on every single run.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command, Mounts
from pyinfra.operations import files, server

import pkgmgr

SSHFS_MOUNTS = [
    {
        "remote": "sam@homeserver:/data",
        "mount_point": "/mnt/homeserver-data",
    },
]

def _ensure_root_known_host(remote_host: str):
    scanned_keys = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command=f"ssh-keyscan {remote_host} 2>/dev/null"
    )
    if not scanned_keys:
        raise ValueError(f"Could not scan SSH host key for {remote_host}")

    for line in scanned_keys.strip().splitlines():
        if line.startswith("#"):
            continue
        key_type = line.split()[1]
        files.line(
            name=f"Add {remote_host} ({key_type}) to root's known_hosts",
            path="/root/.ssh/known_hosts",
            line=rf"^{remote_host} {key_type} .*$",
            replace=line,
            extended_regex=True,
        )

@deploy("Configure SSHFS mounts")
def deploy_sshfs_mounts():
    username = host.data.username
    pkgmgr.install(name="Install sshfs client", packages=["sshfs"])

    files.directory(name="Create /root/.ssh", path="/root/.ssh", mode="700")

    uid = host.get_fact(Command, command=f"id -u {username}") # pyright: ignore[reportUnknownMemberType]
    gid = host.get_fact(Command, command=f"id -g {username}") # pyright: ignore[reportUnknownMemberType]

    for mount in SSHFS_MOUNTS:
        remote_host = mount["remote"].split("@", 1)[1].split(":", 1)[0]
        _ensure_root_known_host(remote_host)

        files.directory(
            name=f"Create {mount['mount_point']}",
            path=mount["mount_point"],
            mode="755",
        )

        identity_file = f"/home/{username}/.ssh/homeserver"
        opts = (
            "defaults,_netdev,allow_other,reconnect,"
            "ServerAliveInterval=15,ServerAliveCountMax=3,"
            f"IdentityFile={identity_file},uid={uid.strip()},gid={gid.strip()}"
        )
        files.line(
            name=f"Add {mount['mount_point']} to fstab",
            path="/etc/fstab",
            line=rf"^\S+\s+{mount['mount_point']}\s+fuse\.sshfs\s+.*$",
            replace=f"{mount['remote']}  {mount['mount_point']}  fuse.sshfs  {opts}  0  0",
            extended_regex=True,
        )

        mounts = host.get_fact(Mounts) # pyright: ignore[reportUnknownMemberType]
        if mount["mount_point"] in mounts:
            host.noop(f"{mount['mount_point']} is already mounted")
        else:
            server.shell(
                name=f"Mount {mount['mount_point']}",
                commands=[
                    f"mount -t fuse.sshfs -o {opts} {mount['remote']} {mount['mount_point']}"
                ],
            )

deploy_sshfs_mounts()
