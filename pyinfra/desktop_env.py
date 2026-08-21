"""Desktop environment abstraction - the only place that dispatches on which desktop
environment a host is running, same pattern as pkgmgr.py owning host.data.distro. Modules
that behave differently per desktop environment (panel/taskbar layout, compositor settings,
...) dispatch on DesktopEnvironment rather than on PackageManager or Distro - a distro
switching desktop environments, or two distros sharing one, shouldn't require touching those
modules.

Autodetected via DesktopEnvironmentFact rather than a group_data var - unlike distro (which
pyinfra/vault.py's SSH login needs before a single command has run) the desktop environment is
cheaply and reliably readable off the live host, so there's nothing for a human to keep in
sync. Detection checks for each DE's own shell session binary (plasmashell/cinnamon) being on
PATH - true whether or not a graphical session is currently active, unlike $XDG_CURRENT_DESKTOP
which is only set inside one (confirmed empty over a plain SSH exec against mint_vm).
"""

from enum import Enum, auto

from typing_extensions import override

from pyinfra.api.facts import FactBase
from pyinfra.context import host

class DesktopEnvironment(Enum):
    KDE_PLASMA = auto()
    CINNAMON = auto()

_DETECTION_COMMANDS = {
    "plasmashell": DesktopEnvironment.KDE_PLASMA,
    "cinnamon": DesktopEnvironment.CINNAMON,
}

class DesktopEnvironmentFact(FactBase[DesktopEnvironment | None]):
    """The host's desktop environment, or None if none of the known session binaries are on
    PATH (e.g. a headless host)."""

    @override
    def command(self) -> str:
        checks = "; ".join(
            f"command -v {binary} >/dev/null 2>&1 && echo {binary}"
            for binary in _DETECTION_COMMANDS
        )
        return f"{checks}; true"

    @override
    def process(self, output: list[str]) -> DesktopEnvironment | None:
        return _DETECTION_COMMANDS.get(output[0]) if output else None

def get_desktop_environment() -> DesktopEnvironment:
    desktop_environment = host.get_fact(DesktopEnvironmentFact) # pyright: ignore[reportUnknownMemberType]
    if desktop_environment is None:
        raise ValueError(
            f"{host.name} has no recognized desktop environment (checked: "
            f"{', '.join(_DETECTION_COMMANDS)}) - can't run a module that dispatches on one"
        )
    return desktop_environment
