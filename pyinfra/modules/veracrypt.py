"""VeraCrypt - disk encryption. No apt/dnf repo - GitHub releases ship a per-Fedora/Ubuntu-release
rpm/deb (like cinc_auditor.py's downloads.cinc.sh situation), so this module branches on
PackageManager directly to build the right download URL.

Only installs when VeraCrypt isn't present yet (checked via `command -v veracrypt`) - grabs
whatever's currently latest for that one-time install, but
deliberately never force-upgrades an already-installed copy on later runs.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import apt, dnf, files

import pkgmgr
from pkgmgr import PackageManager
from paths import PYINFRA_CACHE_DIR
from github import latest_release_tag

VERACRYPT_TAG_PREFIX = "VeraCrypt_"

def _latest_version() -> str:
    """Bare version number (e.g. "1.26.29") - VeraCrypt's GitHub release tags are
    "VeraCrypt_<version>", but package filenames use the bare version."""
    tag = latest_release_tag("veracrypt/VeraCrypt")
    if not tag.startswith(VERACRYPT_TAG_PREFIX):
        raise ValueError(f"Unexpected VeraCrypt release tag format: {tag!r}")
    return tag.removeprefix(VERACRYPT_TAG_PREFIX)

def _release_url(version: str, filename: str) -> str:
    return f"https://github.com/veracrypt/VeraCrypt/releases/download/{VERACRYPT_TAG_PREFIX}{version}/{filename}"

def _download_veracrypt_package(url: str, filename: str) -> str:
    """Same rationale as cinc_auditor.py's _download_cinc_auditor_package: download to
    PYINFRA_CACHE_DIR (survives a reboot, unlike apt.deb/dnf.rpm's own pyinfra-managed /tmp
    download) so a version-comparison idempotency check runs against a file that's actually
    still there, instead of re-downloading (and looking like a change) every run."""
    dest = f"{PYINFRA_CACHE_DIR}/{filename}"
    files.download(name=f"Download VeraCrypt package ({filename})", src=url, dest=dest)
    return dest

def _install_dnf(version: str):
    fedora_version = pkgmgr.get_fedora_version()
    filename = f"veracrypt-{version}-Fedora-{fedora_version}-x86_64.rpm"
    dest = _download_veracrypt_package(_release_url(version, filename), filename)
    dnf.rpm(name="Install VeraCrypt", src=dest)

def _install_apt(version: str):
    ubuntu_release = pkgmgr.get_ubuntu_release()
    filename = f"veracrypt-{version}-Ubuntu-{ubuntu_release}-amd64.deb"
    dest = _download_veracrypt_package(_release_url(version, filename), filename)
    apt.deb(name="Install VeraCrypt", src=dest)

@deploy("Install VeraCrypt")
def deploy_veracrypt():
    already_installed = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="command -v veracrypt || true"
    )
    if already_installed:
        host.noop("VeraCrypt is already installed")
        return

    version = _latest_version()
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            _install_dnf(version)
        case PackageManager.APT:
            _install_apt(version)
        case _:
            assert_never(pm)

deploy_veracrypt()
