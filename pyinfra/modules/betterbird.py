"""Betterbird - Thunderbird fork, email client. Package itself (eu.betterbird.Betterbird) is
installed by base.py via host.data.flatpaks; this module only pins it to the panel.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]

from panel_pin import pin_to_panel

BETTERBIRD_DESKTOP_FILE_ID = "eu.betterbird.Betterbird.desktop"

@deploy("Pin Betterbird to panel")
def pin_betterbird_to_panel():
    pin_to_panel(BETTERBIRD_DESKTOP_FILE_ID, host.data.username)

pin_betterbird_to_panel()
