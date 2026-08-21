"""Double Commander - dual-pane file manager. No apt/dnf packaging at all - a
GitHub-release .tar.xz extracted into a version-suffixed /opt dir and symlinked onto PATH.
"""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files

from archives import download_and_extract
from panel_pin import pin_to_panel

CONFIG_FILES = ["doublecmd.xml", "localconfig.xml", "multiarc.ini", "shortcuts.scf"]
DOUBLECMD_DESKTOP_FILE_ID = "doublecmd.desktop"

def _desktop_entry_content(username: str) -> str:
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Double Commander\n"
        "Comment=Dual-pane file manager\n"
        "Exec=/usr/local/bin/doublecmd %f\n"
        f"Icon=/home/{username}/.local/share/icons/doublecmd.svg\n"
        "Terminal=false\n"
        "Categories=Utility;FileManager;\n"
        "MimeType=inode/directory;\n"
    )

def _install_binary(version: str) -> str:
    extract_dir = f"/opt/doublecmd-{version}"
    binary = f"{extract_dir}/doublecmd/doublecmd"
    download_and_extract(
        name="Download and extract Double Commander",
        url=(
            "https://github.com/doublecmd/doublecmd/releases/download/"
            f"v{version}/doublecmd-{version}.qt.x86_64.tar.xz"
        ),
        dest=extract_dir,
        creates=binary,
    )
    files.link(
        name="Link Double Commander binary into /usr/local/bin",
        path="/usr/local/bin/doublecmd",
        target=binary,
    )
    files.file(
        name="Remove doublecmd.inf to use user config directory",
        path=f"{extract_dir}/doublecmd/settings/doublecmd.inf",
        present=False,
    )
    return binary

def _install_desktop_entry(username: str):
    files.download(
        name="Download Double Commander icon",
        src=(
            "https://raw.githubusercontent.com/doublecmd/doublecmd/refs/heads/master/"
            "pixmaps/mainicon/dc_256.svg"
        ),
        dest=f"/home/{username}/.local/share/icons/doublecmd.svg",
        user=username,
        group=username,
        mode="644",
        _sudo=False,
    )

    files.put(
        name="Create desktop entry for Double Commander",
        src=StringIO(_desktop_entry_content(username)),
        dest=f"/home/{username}/.local/share/applications/doublecmd.desktop",
        user=username,
        group=username,
        mode="644",
        _sudo=False,
    )

def _install_config(username: str):
    files.directory(
        name="Create ~/.config/doublecmd",
        path=f"/home/{username}/.config/doublecmd",
        user=username,
        group=username,
        mode="755",
        _sudo=False,
    )

    for config_file in CONFIG_FILES:
        files.put(
            name=f"Copy Double Commander {config_file}",
            src=f"files/doublecmd/{config_file}",
            dest=f"/home/{username}/.config/doublecmd/{config_file}",
            user=username,
            group=username,
            mode="644",
            _sudo=False,
        )

@deploy("Install Double Commander")
def deploy_doublecmd():
    username = host.data.username
    _install_binary(host.data.doublecmd_version)
    _install_desktop_entry(username)
    _install_config(username)

@deploy("Pin Double Commander to panel")
def pin_doublecmd_to_panel():
    pin_to_panel(DOUBLECMD_DESKTOP_FILE_ID, host.data.username)

deploy_doublecmd()
pin_doublecmd_to_panel()
