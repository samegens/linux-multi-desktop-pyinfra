"""Cinc Auditor (open-source InSpec fork) - used to run this repo's own Inspec controls.
downloads.cinc.sh has no distro repo, only
a pinned-version rpm/deb per release, so this module branches on PackageManager directly to build
the right download URL.
"""

from typing import Generator, assert_never

from pyinfra.context import host
from pyinfra.api.command import StringCommand
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.api.operation import operation # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Arch, Command
from pyinfra.operations import apt, dnf, files

import pkgmgr
from pkgmgr import DEB_ARCH_MAP, PackageManager

@deploy("Install Cinc Auditor")
def deploy_cinc_auditor():
    version = host.data.cinc_auditor_version
    pm = pkgmgr.get_package_manager()

    match pm:
        case PackageManager.DNF:
            # Fedora has no native cinc-auditor build - use the el/9 (RHEL 9) rpm.
            arch = host.get_fact(Arch) # pyright: ignore[reportUnknownMemberType]
            filename = f"cinc-auditor-{version}-1.el9.{arch}.rpm"
            url = f"https://downloads.cinc.sh/files/stable/cinc-auditor/{version}/el/9/{filename}"
            dnf.rpm(name="Install Cinc Auditor", src=_download_cinc_auditor_package(url, filename))
        case PackageManager.APT:
            ubuntu_release = pkgmgr.get_ubuntu_release()
            arch = DEB_ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
            filename = f"cinc-auditor_{version}-1_{arch}.deb"
            url = (
                f"https://downloads.cinc.sh/files/stable/cinc-auditor/{version}"
                f"/ubuntu/{ubuntu_release}/{filename}"
            )
            apt.deb(name="Install Cinc Auditor", src=_download_cinc_auditor_package(url, filename))
        case _:
            assert_never(pm)

    _fix_docker_deprecation_regex(
        name="Fix docker resource deprecation regex bug in deprecations.json",
        version=version,
    )

def _download_cinc_auditor_package(url: str, filename: str) -> str:
    """Downloads to /var/cache/pyinfra (created by modules/base.py) instead of letting
    apt.deb/dnf.rpm handle the URL src themselves - they'd otherwise re-download to a
    pyinfra-managed /tmp temp file every run, which doesn't survive a reboot on mint_vm
    (confirmed live: present right after a real install, gone after rebooting the VM). That
    made every post-reboot run look like a real change, since apt.deb/dnf.rpm's own
    version-comparison idempotency check never got to run against an already-downloaded file.

    Passing a plain local path (no URL scheme) as their src makes apt.deb/dnf.rpm skip their
    internal download step and compare this file's version against what's installed directly -
    the same comparison, just against a file that's actually still there.
    """
    dest = f"/var/cache/pyinfra/{filename}"
    files.download(name=f"Download Cinc Auditor package ({filename})", src=url, dest=dest)
    return dest

@operation()
def _fix_docker_deprecation_regex(version: str) -> Generator[StringCommand, None, None]:
    """The installed inspec-core gem ships a bad regex in etc/deprecations.json -
    "docker\\.+" instead of
    "docker.*" - confirmed still present in 7.1.7 on both the el/9 and Ubuntu 24.04 builds, at
    the same /opt/cinc-auditor/.../inspec-core-<version>/etc/ path on both despite the differing
    Ruby version underneath.

    Facts are gathered for every queued operation during pyinfra's Preparing-operations stage,
    before any operation's commands actually execute - so on a host that's never had Cinc Auditor
    installed before, this `find` always runs against a not-yet-existing /opt/cinc-auditor,
    regardless of where this operation sits in all.py's module order. Skip cleanly in that case
    instead of raising - dnf.rpm/apt.deb's install still runs normally this pass, and the following
    pass (every module's dev loop already requires a second run to confirm idempotency - see
    CLAUDE.md) finds the now-installed gem dir and applies the fix.

    Composes with files.replace's own generator via `_inner` (the same technique pyinfra's own
    operations use, e.g. server.py's yield-from-files.replace._inner) rather than python.call,
    since python.call's FunctionCommand always counts as "executed" just by running - it would
    make this operation report as changed on every single run, breaking idempotency, even when
    files.replace's own diff correctly finds nothing to fix.
    """
    inspec_core_dir = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            "find /opt/cinc-auditor/embedded/lib/ruby/gems -type d "
            f"-name inspec-core-{version} 2>/dev/null || true"
        ),
    )
    if not inspec_core_dir:
        return

    yield from files.replace._inner( # pyright: ignore[reportPrivateUsage, reportUnknownMemberType]
        path=f"{inspec_core_dir.strip()}/etc/deprecations.json",
        text=r'"docker\.+"',
        replace='"docker.*"',
    )

deploy_cinc_auditor()
