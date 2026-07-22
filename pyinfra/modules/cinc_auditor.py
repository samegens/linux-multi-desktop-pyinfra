"""Cinc Auditor (open-source InSpec fork) - used to run this repo's own Inspec controls.
downloads.cinc.sh has no distro repo, only
a pinned-version rpm/deb per release, so this module branches on PackageManager directly to build
the right download URL.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Arch, Command
from pyinfra.operations import apt, dnf, files, python

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
            dnf.rpm(
                name="Install Cinc Auditor",
                src=(
                    f"https://downloads.cinc.sh/files/stable/cinc-auditor/{version}"
                    f"/el/9/cinc-auditor-{version}-1.el9.{arch}.rpm"
                ),
            )
        case PackageManager.APT:
            ubuntu_release = pkgmgr.get_ubuntu_release()
            arch = DEB_ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
            apt.deb(
                name="Install Cinc Auditor",
                src=(
                    f"https://downloads.cinc.sh/files/stable/cinc-auditor/{version}"
                    f"/ubuntu/{ubuntu_release}/cinc-auditor_{version}-1_{arch}.deb"
                ),
            )
        case _:
            assert_never(pm)

    python.call( # pyright: ignore[reportUnknownMemberType]
        name="Fix docker resource deprecation regex bug in deprecations.json",
        function=_fix_docker_deprecation_regex,
        version=version,
    )

def _fix_docker_deprecation_regex(version: str):
    """The installed inspec-core gem ships a bad regex in etc/deprecations.json -
    "docker\\.+" instead of
    "docker.*" - confirmed still present in 7.1.7 on both the el/9 and Ubuntu 24.04 builds, at
    the same /opt/cinc-auditor/.../inspec-core-<version>/etc/ path on both despite the differing
    Ruby version underneath.

    Runs via python.call so the `find` fact and the fix below execute after the install
    operation above has actually run on the target - a bare host.get_fact() call here would run
    eagerly at deploy-build time, before dnf.rpm/apt.deb's install actually happens, and fail with
    "No such file or directory" on any host that doesn't already have Cinc Auditor installed.
    """
    inspec_core_dir = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            "find /opt/cinc-auditor/embedded/lib/ruby/gems -type d "
            f"-name inspec-core-{version}"
        ),
    )
    if not inspec_core_dir:
        raise ValueError(
            f"Could not locate inspec-core-{version} gem dir under /opt/cinc-auditor - "
            "Cinc Auditor install may have failed or changed layout"
        )

    files.replace( # pyright: ignore[reportUnknownMemberType]
        name="Fix docker resource deprecation regex bug in deprecations.json",
        path=f"{inspec_core_dir.strip()}/etc/deprecations.json",
        text=r'"docker\.+"',
        replace='"docker.*"',
    )

deploy_cinc_auditor()
