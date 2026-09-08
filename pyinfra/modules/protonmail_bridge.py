"""Proton Mail Bridge - local IMAP/SMTP bridge for Proton Mail, used by Betterbird. The flatpak
package itself (ch.protonmail.protonmail-bridge) is installed by base.py via host.data.flatpaks,
like Betterbird - this module only adds the autostart entry, since the package being present
doesn't mean it's actually running for Betterbird to connect to.
"""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files

AUTOSTART_DESKTOP_ENTRY = (
    "[Desktop Entry]\n"
    "Type=Application\n"
    "Version=1.1\n"
    "Name=Proton Mail Bridge\n"
    "GenericName=Proton Mail Bridge for Linux\n"
    "Comment=Proton Mail Bridge is a desktop application that runs in the background, "
    "encrypting and decrypting messages as they enter and leave your computer.\n"
    "Icon=ch.protonmail.protonmail-bridge\n"
    "Exec=/usr/bin/flatpak run --branch=stable --arch=x86_64 "
    "--command=protonmail-bridge ch.protonmail.protonmail-bridge\n"
    "Terminal=false\n"
    "Categories=Office;Email\n"
    "StartupWMClass=Proton Mail Bridge\n"
    "X-Desktop-File-Install-Version=0.28\n"
    "X-Flatpak=ch.protonmail.protonmail-bridge\n"
)

def _install_autostart_entry(username: str):
    files.directory(
        name="Create ~/.config/autostart",
        path=f"/home/{username}/.config/autostart",
        user=username,
        group=username,
        mode="755",
        _sudo=False,
    )
    files.put(
        name="Create Proton Mail Bridge autostart entry",
        src=StringIO(AUTOSTART_DESKTOP_ENTRY),
        dest=f"/home/{username}/.config/autostart/ch.protonmail.protonmail-bridge.desktop",
        user=username,
        group=username,
        mode="644",
        _sudo=False,
    )

@deploy("Install Proton Mail Bridge")
def deploy_protonmail_bridge():
    _install_autostart_entry(host.data.username)

deploy_protonmail_bridge()
