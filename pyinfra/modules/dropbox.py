"""Dropbox - cloud sync client with Nautilus/GNOME Files integration. Installed from Dropbox's
own apt/dnf repo (not a distro-packaged build), so it always tracks whatever version is
currently there - deliberately unpinned, same rationale as fastfetch.py's apt branch.

The package name itself differs by manager - not a distro property, a Dropbox packaging one:
their apt archive renamed the historical "nautilus-dropbox" package to "dropbox" (Provides/
Replaces/Breaks: nautilus-dropbox, same PGP signing key confirmed via `gpg --verify` against
both repos' Release files), but their dnf repo never got the same rename and still only ships
nautilus-dropbox-*.rpm (confirmed live: linux.dropbox.com/fedora/<release>/ has no "dropbox"
package at all). Handled via PACKAGE_NAME_OVERRIDES like any other apt/dnf name divergence.

Also installs python3-gpg explicitly - the Dropbox installer needs it to verify its own binary
signatures, but it's only an apt Suggests (not a hard Depends), so a plain package install
wouldn't pull it in.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.facts.server import Arch
from pyinfra.operations import apt, dnf

import pkgmgr
from pkgmgr import DEB_ARCH_MAP, PackageManager

DROPBOX_GPG_KEY_URL = "https://linux.dropbox.com/fedora/rpm-public-key.asc"
APT_KEYRING_PATH = "/etc/apt/keyrings/dropbox.gpg"

def _ensure_apt_repo():
    repo_file = "/etc/apt/sources.list.d/dropbox.list"
    if host.get_fact(File, path=repo_file): # pyright: ignore[reportUnknownMemberType]
        host.noop("Dropbox apt repo already configured")
        return

    apt.key(name="Add Dropbox apt GPG key", src=DROPBOX_GPG_KEY_URL, dest="dropbox.gpg")
    codename = pkgmgr.get_ubuntu_codename()
    arch = DEB_ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
    apt.repo(
        name="Add Dropbox apt repo",
        src=(
            f"deb [arch={arch} signed-by={APT_KEYRING_PATH}] "
            f"https://linux.dropbox.com/ubuntu {codename} main"
        ),
        filename="dropbox",
    )
    # Force a real refresh - base.py already ran apt.update(cache_time=3600) earlier in the
    # full deploy, so the routine cached update wouldn't pick up this brand new source until
    # the cache_time window expires. Same fix as docker.py's _ensure_apt_repo().
    apt.update(name="Refresh apt cache for new Dropbox repo")

def _ensure_dnf_repo():
    dnf.repo(
        name="Add Dropbox dnf repo",
        src="dropbox",
        baseurl="https://linux.dropbox.com/fedora/$releasever/",
        description="Dropbox Repository",
        gpgcheck=True,
        gpgkey=DROPBOX_GPG_KEY_URL,
    )

@deploy("Install Dropbox")
def deploy_dropbox():
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.APT:
            _ensure_apt_repo()
        case PackageManager.DNF:
            _ensure_dnf_repo()
        case _:
            assert_never(pm)

    # python3-gpg isn't a hard Depends of the apt "dropbox" package (only a Suggests, per
    # linux.dropbox.com/ubuntu's Packages index) - without it the installer can't verify its
    # own binary signatures and silently skips that check. Same package name on both managers,
    # no PACKAGE_NAME_OVERRIDES entry needed (confirmed via `dnf info`/`apt-cache policy`).
    pkgmgr.install(name="Install Dropbox signature verification dependency", packages=["python3-gpg"])
    pkgmgr.install(name="Install Dropbox", packages=["dropbox"])

deploy_dropbox()
