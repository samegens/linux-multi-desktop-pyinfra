"""Right Alt as compose key, for building special/accented characters.
"""

import re
from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

import pkgmgr
from pkgmgr import PackageManager

COMPOSE_OPTION = "compose:ralt"

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
# overwriting it. Mint's apt targets are Cinnamon-only today, so this rides along with the apt
# branch rather than needing its own desktop_environment dispatch.
CINNAMON_INPUT_SOURCES_SCHEMA = "org.cinnamon.desktop.input-sources"
CINNAMON_XKB_OPTIONS_DCONF_PATH = "/org/cinnamon/desktop/input-sources/xkb-options"

def _get_gsettings_list(schema: str, key: str) -> list[str]:
    output = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command=f"gsettings get {schema} {key}"
    )
    return re.findall(r"'([^']*)'", output) if output else []

def _set_compose_key_cinnamon():
    options = _get_gsettings_list(CINNAMON_INPUT_SOURCES_SCHEMA, "xkb-options")

    if COMPOSE_OPTION in options:
        host.noop("Right Alt is already the compose key (Cinnamon)")
        return

    new_value = "[" + ", ".join(f"'{option}'" for option in [*options, COMPOSE_OPTION]) + "]"

    # gsettings/dconf writes go through a per-user dconf-service reached over the D-Bus session
    # bus - over a plain SSH exec there's no session bus to autolaunch, so a bare `gsettings set`
    # or `dconf write` silently no-ops (exit 0, value never persists; confirmed live against
    # mint_vm). `dbus-run-session` gives the write its own private bus so it actually lands.
    server.shell(
        name="Set right Alt as compose key in Cinnamon settings",
        commands=[
            f'dbus-run-session -- dconf write {CINNAMON_XKB_OPTIONS_DCONF_PATH} "{new_value}"'
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
            _set_compose_key_cinnamon()
        case _:
            assert_never(pm)

deploy_keyboard()
