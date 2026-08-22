"""Fastfetch - neofetch-like system info tool. Packaged in Fedora's own repos (dnf always
installs whatever's current there), but not in Ubuntu/Mint's (confirmed live against mint_vm:
no such package in apt-cache search/policy, noble/universe only carries the deprecated
neofetch) - so the apt side pulls fastfetch-cli/fastfetch's latest GitHub release .deb instead,
same download-a-.deb pattern as ghostty.py's apt branch. Deliberately unpinned (unlike
ghostty_apt_version/cinc_auditor_version) - always installs whatever's current, matching the
dnf side's behaviour.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files

import pkgmgr
from pkgmgr import PackageManager
from paths import PYINFRA_CACHE_DIR

def _get_latest_apt_version() -> str:
    # /releases/latest redirects to /releases/tag/<version> - resolving that (not the GitHub
    # API) avoids the API's 60-requests/hour unauthenticated rate limit.
    url = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            "curl -sI -L -o /dev/null -w '%{url_effective}' "
            "https://github.com/fastfetch-cli/fastfetch/releases/latest"
        ),
    )
    if not url:
        raise ValueError("Could not resolve latest Fastfetch release")
    return url.rstrip("/").rsplit("/", 1)[-1]

def _install_apt():
    version = _get_latest_apt_version()
    filename = "fastfetch-linux-amd64.deb"
    url = f"https://github.com/fastfetch-cli/fastfetch/releases/download/{version}/{filename}"
    dest = f"{PYINFRA_CACHE_DIR}/fastfetch-{version}-linux-amd64.deb"
    files.download(name=f"Download Fastfetch package ({filename})", src=url, dest=dest)
    apt.deb(name="Install Fastfetch", src=dest)

@deploy("Install Fastfetch")
def deploy_fastfetch():
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            pkgmgr.install(name="Install Fastfetch", packages=["fastfetch"])
        case PackageManager.APT:
            _install_apt()
        case _:
            assert_never(pm)

deploy_fastfetch()
