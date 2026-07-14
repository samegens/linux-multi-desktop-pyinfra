"""Starship prompt."""

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import Arch
from pyinfra.operations import apt, files

ARCH_MAP = {
    "x86_64": "x86_64",
    "aarch64": "aarch64",
}


@deploy("Install and configure Starship")
def deploy_starship():
    apt.packages(name="Install powerline fonts", packages=["fonts-powerline"], present=True)

    files.put(
        name="Copy starship config",
        src="files/etc/starship.toml",
        dest="/etc/starship.toml",
        mode="644",
    )

    arch = ARCH_MAP[host.get_fact(Arch)]
    files.download(
        name="Download starship binary",
        src=f"https://github.com/starship/starship/releases/download/"
        f"{host.data.starship_version}/starship-{arch}-unknown-linux-musl.tar.gz",
        dest="/tmp/starship.tar.gz",
    )
    files.unarchive(
        name="Extract starship",
        src="/tmp/starship.tar.gz",
        dest="/usr/local/bin",
        remote_src=True,
    )

    files.block(
        name="Configure Starship prompt for all users",
        path="/etc/bash.bashrc",
        content='export STARSHIP_CONFIG=/etc/starship.toml\neval "$(starship init bash)"',
        marker="# {mark} PYINFRA MANAGED BLOCK - STARSHIP",
    )
