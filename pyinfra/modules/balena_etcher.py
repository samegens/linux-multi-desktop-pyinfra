"""balenaEtcher - flash OS images to USB/SD.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import apt, dnf, files

import pkgmgr
from pkgmgr import DEB_ARCH_MAP, PackageManager

@deploy("Install balenaEtcher")
def deploy_balena_etcher():
    version = host.data.balena_etcher_version
    pm = pkgmgr.get_package_manager()

    match pm:
        case PackageManager.DNF:
            filename = f"balena-etcher-{version}-1.x86_64.rpm"
            url = (
                f"https://github.com/balena-io/etcher/releases/download/v{version}/{filename}"
            )
            dnf.rpm(
                name="Install balenaEtcher", src=_download_balena_etcher_package(url, filename)
            )
        case PackageManager.APT:
            arch = DEB_ARCH_MAP["x86_64"]
            filename = f"balena-etcher_{version}_{arch}.deb"
            url = (
                f"https://github.com/balena-io/etcher/releases/download/v{version}/{filename}"
            )
            apt.deb(
                name="Install balenaEtcher", src=_download_balena_etcher_package(url, filename)
            )
        case _:
            assert_never(pm)

def _download_balena_etcher_package(url: str, filename: str) -> str:
    """Downloads to /var/cache/pyinfra (created by modules/base.py) instead of letting apt.deb/
    dnf.rpm handle the URL src themselves - see modules/cinc_auditor.py's
    _download_cinc_auditor_package for why (doesn't survive a reboot on mint_vm as a pyinfra-
    managed /tmp file, breaking idempotency)."""
    dest = f"/var/cache/pyinfra/{filename}"
    files.download(name=f"Download balenaEtcher package ({filename})", src=url, dest=dest)
    return dest

deploy_balena_etcher()
