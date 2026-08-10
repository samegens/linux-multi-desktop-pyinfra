"""Ghostty - GPU-accelerated terminal emulator. No official Linux packages at all 
so this module branches on PackageManager
directly to reach the two community-maintained sources:
- the scottames/ghostty Fedora COPR for dnf,
- the mkasberg/ghostty-ubuntu project's per-release .deb for apt.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import apt, dnf, files
from pyinfra.facts.server import Arch

import pkgmgr
from pkgmgr import DEB_ARCH_MAP, PackageManager
from keyfile import set_key_value
from paths import PYINFRA_CACHE_DIR

DNF_COPR_OWNER = "scottames"
DNF_COPR_PROJECT = "ghostty"

# key -> value, exactly as ghostty's own config parser expects them (whitespace around "="
# doesn't matter to ghostty itself, but keyfile.set_key_value always writes key=value with
# none - see keyfile.py).
GHOSTTY_CONFIG_SETTINGS: dict[str, str] = {
    "maximize": "true",
}

def _install_dnf():
    dnf.repo(
        name="Add ghostty dnf repo",
        src="ghostty",
        baseurl=(
            f"https://download.copr.fedorainfracloud.org/results/{DNF_COPR_OWNER}/{DNF_COPR_PROJECT}"
            "/fedora-$releasever-$basearch/"
        ),
        description=f"Copr repo for {DNF_COPR_PROJECT} owned by {DNF_COPR_OWNER}",
        gpgcheck=True,
        gpgkey=(
            f"https://download.copr.fedorainfracloud.org/results/{DNF_COPR_OWNER}/{DNF_COPR_PROJECT}"
            "/pubkey.gpg"
        ),
    )
    dnf.packages(name="Install Ghostty", packages=["ghostty"])

def _deb_version(tag: str) -> str:
    """The .deb filename's version component, derived from the GitHub release tag - e.g. tag
    "1.3.1-0-ppa2" -> "1.3.1-0.ppa2" (confirmed against every mkasberg/ghostty-ubuntu release
    to date: the last "-" before "ppaN" is always a "." in the actual package version,
    Debian's version format disallowing a second dash in the upstream-version component)."""
    base, ppa_suffix = tag.rsplit("-", 1)
    return f"{base}.{ppa_suffix}"

def _install_apt(tag: str):
    ubuntu_release = pkgmgr.get_ubuntu_release()
    arch = DEB_ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
    filename = f"ghostty_{_deb_version(tag)}_{arch}_{ubuntu_release}.deb"
    url = f"https://github.com/mkasberg/ghostty-ubuntu/releases/download/{tag}/{filename}"
    dest = f"{PYINFRA_CACHE_DIR}/{filename}"
    files.download(name=f"Download Ghostty package ({filename})", src=url, dest=dest)
    apt.deb(name="Install Ghostty", src=dest)

def _install_config(username: str):
    config_dir = f"/home/{username}/.config/ghostty"
    files.directory(
        name="Create ~/.config/ghostty",
        path=config_dir,
        user=username,
        group=username,
        mode="755",
        _sudo=False,
    )

    for key, value in GHOSTTY_CONFIG_SETTINGS.items():
        set_key_value(
            name=f"Set Ghostty setting {key}={value}",
            path=f"{config_dir}/config.ghostty",
            key=key,
            value=value,
            _sudo=False,
        )

@deploy("Install Ghostty")
def deploy_ghostty():
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            _install_dnf()
        case PackageManager.APT:
            _install_apt(host.data.ghostty_apt_version)
        case _:
            assert_never(pm)

    _install_config(host.data.username)

deploy_ghostty()
