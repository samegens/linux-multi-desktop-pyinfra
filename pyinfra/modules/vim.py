"""Vim - global vimrc.local, downloaded from the same dotfiles repo used for other machines."""

from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files

from paths import SystemPath, get_system_path

VIMRC_URL = "https://raw.githubusercontent.com/samegens/dotfiles/master/.vimrc"

@deploy("Install and configure Vim")
def deploy_vim():
    files.download(
        name="Download global vimrc.local",
        src=VIMRC_URL,
        dest=get_system_path(SystemPath.VIMRC_LOCAL),
        mode="644",
    )

deploy_vim()
