"""Bind Super+L to lock the screen.

Cinnamon ships Super+L bound to its Looking Glass debugger instead
(org.cinnamon.desktop.keybindings looking-glass-keybinding) - this frees that binding and adds
Super+L to the existing lock/screensaver keybinding (org.cinnamon.desktop.keybindings.media-keys
screensaver) instead of replacing it, so the existing Ctrl+Alt+L / XF86ScreenSaver bindings keep
working too. KDE Plasma already binds Meta+L to "Lock Session" out of the box - confirmed live
against localhost - so there's nothing to configure there.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import server

import gsettings
from dbus_session import get_write_command_prefix
from desktop_env import DesktopEnvironment, get_desktop_environment

LOOKING_GLASS_SCHEMA = "org.cinnamon.desktop.keybindings"
LOOKING_GLASS_KEY = "looking-glass-keybinding"
LOOKING_GLASS_DCONF_PATH = "/org/cinnamon/desktop/keybindings/looking-glass-keybinding"

SCREENSAVER_SCHEMA = "org.cinnamon.desktop.keybindings.media-keys"
SCREENSAVER_KEY = "screensaver"
SCREENSAVER_DCONF_PATH = "/org/cinnamon/desktop/keybindings/media-keys/screensaver"

SUPER_L = "<Super>l"

def _unbind_looking_glass(prefix: str) -> str | None:
    bindings = gsettings.get_list(LOOKING_GLASS_SCHEMA, LOOKING_GLASS_KEY)
    if SUPER_L not in bindings:
        return None

    new_value = gsettings.format_list([b for b in bindings if b != SUPER_L])
    return f'{prefix} dconf write {LOOKING_GLASS_DCONF_PATH} "{new_value}"'

def _bind_lock_screen(prefix: str) -> str | None:
    bindings = gsettings.get_list(SCREENSAVER_SCHEMA, SCREENSAVER_KEY)
    if SUPER_L in bindings:
        return None

    new_value = gsettings.format_list([*bindings, SUPER_L])
    return f'{prefix} dconf write {SCREENSAVER_DCONF_PATH} "{new_value}"'

def _set_lock_screen_shortcut_cinnamon(username: str):
    prefix = get_write_command_prefix(username)
    commands = [c for c in [_unbind_looking_glass(prefix), _bind_lock_screen(prefix)] if c]
    if not commands:
        host.noop("Super+L is already bound to lock the screen (Cinnamon)")
        return

    server.shell(
        name="Bind Super+L to lock the screen in Cinnamon settings",
        commands=commands,
        _sudo=False,
    )

@deploy("Bind Super+L to lock the screen")
def deploy_lock_screen_shortcut():
    desktop_environment = get_desktop_environment()
    match desktop_environment:
        case DesktopEnvironment.CINNAMON:
            _set_lock_screen_shortcut_cinnamon(host.data.username)
        case DesktopEnvironment.KDE_PLASMA:
            pass
        case _:
            assert_never(desktop_environment)

deploy_lock_screen_shortcut()
