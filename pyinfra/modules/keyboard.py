"""Right Alt as compose key, for building special/accented characters.
"""

import re
from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

import gsettings
import pkgmgr
from dbus_session import get_write_command_prefix
from pkgmgr import PackageManager
from desktop_env import DesktopEnvironment, get_desktop_environment

COMPOSE_OPTION: str = "compose:ralt"

def _parse_localectl_field(status: str, field: str) -> str:
    match = re.search(rf"^\s*X11 {field}:\s*(.*)$", status, re.MULTILINE)
    return match.group(1).strip() if match else ""

def _set_compose_key_dnf():
    status = host.get_fact(Command, command="localectl status") # pyright: ignore[reportUnknownMemberType]
    options = _parse_localectl_field(status, "Options") if status else ""

    if COMPOSE_OPTION in options.split(","):
        host.noop("Right Alt is already the compose key")
        return

    layout = _parse_localectl_field(status, "Layout") if status else ""
    model = _parse_localectl_field(status, "Model") if status else ""
    variant = _parse_localectl_field(status, "Variant") if status else ""
    new_options = ",".join(filter(None, [options, COMPOSE_OPTION]))

    server.shell(
        name="Set right Alt as compose key",
        commands=[
            f"localectl set-x11-keymap '{layout}' '{model}' '{variant}' '{new_options}'"
        ],
    )

def _set_compose_key_apt():
    """Probably needed to have right alt as compose key before an actual session (login prompt for example)"""
    
    current_line = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="grep '^XKBOPTIONS=' /etc/default/keyboard"
    )

    if current_line and COMPOSE_OPTION in current_line:
        host.noop("Right Alt is already the compose key")
        return

    files.replace( # pyright: ignore[reportUnknownMemberType]
        name="Set right Alt as compose key in /etc/default/keyboard",
        path="/etc/default/keyboard",
        text=r"^XKBOPTIONS=.*$",
        replace=f'XKBOPTIONS="{COMPOSE_OPTION}"',
        extended_regex=True,
    )

# /etc/default/keyboard only seeds the X11 session's initial XKB options - Cinnamon's own
# settings daemon (org.cinnamon.desktop.input-sources, a separate schema from GNOME's, confirmed
# live against mint_vm) re-applies its own xkb-options from GSettings on session start,
# overwriting it.
CINNAMON_INPUT_SOURCES_SCHEMA = "org.cinnamon.desktop.input-sources"
CINNAMON_XKB_OPTIONS_DCONF_PATH = "/org/cinnamon/desktop/input-sources/xkb-options"

def _set_compose_key_cinnamon(username: str):
    options = gsettings.get_list(CINNAMON_INPUT_SOURCES_SCHEMA, "xkb-options")

    if COMPOSE_OPTION in options:
        host.noop("Right Alt is already the compose key (Cinnamon)")
        return

    new_value = gsettings.format_list([*options, COMPOSE_OPTION])
    prefix = get_write_command_prefix(username)

    server.shell(
        name="Set right Alt as compose key in Cinnamon settings",
        commands=[
            f'{prefix} dconf write {CINNAMON_XKB_OPTIONS_DCONF_PATH} "{new_value}"'
        ],
        _sudo=False,
    )

@deploy("Configure keyboard")
def deploy_keyboard():
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            _set_compose_key_dnf()
        case PackageManager.APT:
            _set_compose_key_apt()
        case _:
            assert_never(pm)

    desktop_environment = get_desktop_environment()
    match desktop_environment:
        case DesktopEnvironment.CINNAMON:
            _set_compose_key_cinnamon(host.data.username)
        case DesktopEnvironment.KDE_PLASMA:
            pass
        case _:
            assert_never(desktop_environment)

deploy_keyboard()
