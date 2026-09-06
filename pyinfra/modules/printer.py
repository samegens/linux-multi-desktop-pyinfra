"""Printing via IPP Everywhere (driverless, no printer-specific driver package needed) and
scanning support.

PRINTERS is ported from whatever's actually configured on localhost's live CUPS instance
(/etc/cups/printers.conf) - each entry's `ppd` is a byte-for-byte copy of the PPD CUPS itself
generated there (files/cups/*.ppd), fetched once via `lpadmin -m everywhere` while the device
was reachable. Queues on every other target are created from that same static PPD via
`lpadmin -P <path>` instead of re-running `-m everywhere` - `-P` just registers a local file, so
unlike `-m everywhere` (which queries the live device over IPP to build its capabilities) this
never needs the printer to be powered on or reachable.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

import pkgmgr
from paths import PYINFRA_CACHE_DIR

PACKAGES = ["cups", "sane-utils", "simple-scan"]

PRINTERS = [
    {
        "name": "HP_LaserJet_MFP_M232-M237",
        "uri": "ipps://NPIA62AA9.local:631/ipp/print",
        "location": "zolder",
        "info": "HP LaserJet MFP M232-M237 (driverless)",
        "ppd": "files/cups/HP_LaserJet_MFP_M232-M237.ppd",
    },
]

DEFAULT_PRINTER = "HP_LaserJet_MFP_M232-M237"

def _get_configured_uri(name: str) -> str | None:
    output = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command=f"lpstat -v {name} 2>/dev/null || true"
    )
    # "device for NAME: URI" - only the first colon (right after NAME) should split.
    return output.split(":", 1)[1].strip() if output and ":" in output else None

def _configure_printer_queue(printer: dict[str, str]):
    if _get_configured_uri(printer["name"]) == printer["uri"]:
        host.noop(f"{printer['name']} is already configured")
        return

    staged_ppd = f"{PYINFRA_CACHE_DIR}/{printer['name']}.ppd"
    files.put(
        name=f"Stage {printer['name']}'s PPD",
        src=printer["ppd"],
        dest=staged_ppd,
        mode="644",
    )
    server.shell(
        name=f"Configure {printer['name']} printer queue",
        commands=[
            f"lpadmin -p {printer['name']} -E -v {printer['uri']} -P {staged_ppd} "
            f"-L '{printer['location']}' -D '{printer['info']}'"
        ],
    )

def _set_default_printer():
    current_default = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="lpstat -d 2>/dev/null || true"
    )
    if current_default and current_default.strip().endswith(DEFAULT_PRINTER):
        host.noop(f"{DEFAULT_PRINTER} is already the default printer")
        return

    server.shell(name="Set default printer", commands=[f"lpadmin -d {DEFAULT_PRINTER}"])

@deploy("Install printer/scanner support")
def deploy_printer():
    pkgmgr.install(name="Install CUPS and scanning support", packages=PACKAGES)
    server.service(
        name="Enable and start CUPS",
        service="cups",
        running=True,
        enabled=True,
    )
    for printer in PRINTERS:
        _configure_printer_queue(printer)
    _set_default_printer()

deploy_printer()
