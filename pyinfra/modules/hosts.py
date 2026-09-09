"""Personal /etc/hosts entries. Appended as a single marked block via files.block so the
distro-managed loopback lines above it are never touched.

files.block (still a beta pyinfra operation) writes its result to a temp file and moves it
over the target on any real change - which drops /etc/hosts' SELinux context (net_conf_t)
to the temp file's own context (user_tmp_t), confirmed live on localhost: systemd-resolved
was denied read access (AVC denial) immediately after the first real run, until `restorecon`
fixed the label. Mint has no SELinux, so this is a dnf-only follow-up fix - restorecon is
itself idempotent (no-op once the label's already correct), so it's safe to just always run
it after files.block rather than trying to detect whether the label actually changed.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

import pkgmgr
from pkgmgr import PackageManager

def _restore_selinux_context_if_needed():
    # -n -v: dry run, only prints a relabel line if the context is actually wrong - lets this
    # stay idempotent (a plain `restorecon` always exits 0 with no output either way, giving
    # no signal to gate a real run on).
    needs_relabel = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="restorecon -n -v /etc/hosts 2>/dev/null || true"
    )
    if not needs_relabel:
        host.noop("/etc/hosts already has the correct SELinux context")
        return

    server.shell(name="Restore /etc/hosts SELinux context", commands=["restorecon /etc/hosts"])

@deploy("Configure custom /etc/hosts entries")
def deploy_hosts():
    files.block(
        name="Add custom /etc/hosts entries",
        path="/etc/hosts",
        content="\n".join(host.data.hosts_entries),
        marker="# {mark} PYINFRA MANAGED BLOCK - HOSTS",
    )

    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            _restore_selinux_context_if_needed()
        case PackageManager.APT:
            pass
        case _:
            assert_never(pm)

deploy_hosts()
