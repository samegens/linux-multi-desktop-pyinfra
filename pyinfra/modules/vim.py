"""Vim - global vimrc.local, downloaded from the same dotfiles repo used for other machines.

files.download only re-fetches when a checksum is given and doesn't match the existing
file - with no checksum, it treats an already-present dest as done forever, so a change
pushed to the dotfiles repo would silently never reach hosts that already have the old
copy. Fetching the current sha256 as a fact and passing it as sha256sum makes pyinfra
compare against the live upstream content on every run instead.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files

from paths import SystemPath, get_system_path

VIMRC_URL = "https://raw.githubusercontent.com/samegens/dotfiles/master/.vimrc"

@deploy("Install and configure Vim")
def deploy_vim():
    checksum = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command=f"curl -sL {VIMRC_URL} | sha256sum | cut -d' ' -f1"
    )
    files.download(
        name="Download global vimrc.local",
        src=VIMRC_URL,
        dest=get_system_path(SystemPath.VIMRC_LOCAL),
        sha256sum=checksum.strip() if checksum else None,
        mode="644",
    )

deploy_vim()
