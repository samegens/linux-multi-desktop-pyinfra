"""KeePassXC - password manager. Package itself (keepassxc) is installed by base.py via
host.data.packages; this module only pins it to the panel.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]

from panel_pin import pin_to_panel

KEEPASSXC_DESKTOP_FILE_ID = "org.keepassxc.KeePassXC.desktop"

@deploy("Pin KeePassXC to panel")
def pin_keepassxc_to_panel():
    pin_to_panel(KEEPASSXC_DESKTOP_FILE_ID, host.data.username)

pin_keepassxc_to_panel()
