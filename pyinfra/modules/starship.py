"""Starship prompt."""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Arch
from pyinfra.operations import files

from archives import download_and_extract

import pkgmgr
from paths import SystemPath, get_system_path

ARCH_MAP = {
    "x86_64": "x86_64",
    "aarch64": "aarch64",
}

@deploy("Install and configure Starship")
def deploy_starship():
    pkgmgr.install(name="Install powerline fonts", packages=["fonts-powerline"])

    files.put(
        name="Copy starship config",
        src="files/etc/starship.toml",
        dest="/etc/starship.toml",
        mode="644",
    )

    arch = ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
    download_and_extract(
        name="Download and extract starship binary",
        url=f"https://github.com/starship/starship/releases/download/{host.data.starship_version}/starship-{arch}-unknown-linux-musl.tar.gz",
        dest="/usr/local/bin",
        creates="/usr/local/bin/starship",
    )

    files.block(
        name="Configure Starship prompt for all users",
        path=get_system_path(SystemPath.SYSTEM_BASHRC),
        content='export STARSHIP_CONFIG=/etc/starship.toml\neval "$(starship init bash)"',
        marker="# {mark} PYINFRA MANAGED BLOCK - STARSHIP",
    )

deploy_starship()
