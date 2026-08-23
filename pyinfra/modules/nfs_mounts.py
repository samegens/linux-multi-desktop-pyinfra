"""NFS client mounts - persisted in /etc/fstab and mounted immediately (not just left for the
next boot), so a run of this module leaves the share usable right away.

The client package name differs by manager - not a real functional difference, just a naming
one (confirmed via `dnf info`/`apt-cache policy`: Fedora's nfs-utils vs Debian/Ubuntu's
nfs-common; both ship the same rpcbind/nfs-client.target systemd units under those identical
names on both, confirmed live against mint_vm and localhost, so no services.py entry needed -
same reasoning as k3s.py hardcoding its own service name directly).

"defaults"/"_netdev" are fstab-only pseudo-options (systemd/mount-generator hints, e.g. "wait
for the network before mounting at boot") - not real mount(8) options, so they're only written
into /etc/fstab, never passed to server.mount's options= (which compares against the live
kernel-reported mount options table - passing fstab pseudo-options there would report "changed"
and remount on every single run, since the kernel never reports "_netdev" back).

nfs-client.target is enabled/started via a manual is-active/is-enabled check + server.shell,
not server.service - pyinfra's SystemdStatus fact only recognizes SubState values "running/
waiting/exited/listening/mounted" as "active" (see pyinfra's systemd facts module), but an
active .target unit's own SubState is literally "active", which isn't in that list. That makes
server.service(running=True) treat an already-active target as not running and re-issue
`systemctl start` on every single run - confirmed live against localhost (rpcbind, a regular
.service with SubState "running", was correctly idempotent; nfs-client.target was not).
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

import pkgmgr

NFS_MOUNTS = [
    {
        "src": "cubi:/data/public",
        "mount_point": "/mnt/homeserver-public",
        "opts": "defaults,_netdev",
    },
]

def _ensure_nfs_client_target():
    is_active = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="systemctl is-active nfs-client.target || true"
    )
    is_enabled = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="systemctl is-enabled nfs-client.target || true"
    )
    if is_active and is_active.strip() == "active" and is_enabled and is_enabled.strip() == "enabled":
        host.noop("nfs-client.target is already active and enabled")
        return

    server.shell(
        name="Enable and start nfs-client.target",
        commands=["systemctl enable --now nfs-client.target"],
    )

@deploy("Configure NFS mounts")
def deploy_nfs_mounts():
    pkgmgr.install(name="Install NFS client packages", packages=["nfs-common", "rpcbind"])

    server.service(name="Enable rpcbind service", service="rpcbind", running=True, enabled=True)
    _ensure_nfs_client_target()

    for mount in NFS_MOUNTS:
        files.directory(
            name=f"Create {mount['mount_point']}",
            path=mount["mount_point"],
            mode="755",
        )

        files.line(
            name=f"Add {mount['mount_point']} to fstab",
            path="/etc/fstab",
            line=rf"^\S+\s+{mount['mount_point']}\s+nfs\s+.*$",
            replace=f"{mount['src']}  {mount['mount_point']}  nfs  {mount['opts']}  0  0",
            extended_regex=True,
        )

        server.mount(
            name=f"Mount {mount['mount_point']}",
            path=mount["mount_point"],
            mounted=True,
            device=mount["src"],
            fs_type="nfs",
        )

deploy_nfs_mounts()
