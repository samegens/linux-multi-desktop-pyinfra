"""Workrave - RSI break reminder.
"""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

import pkgmgr
from dbus_session import get_dbus_env, resolve_uid

AUTOSTART_DESKTOP_ENTRY = (
    "[Desktop Entry]\n"
    "Type=Application\n"
    "Exec=workrave\n"
    "Hidden=false\n"
    "NoDisplay=false\n"
    "X-GNOME-Autostart-enabled=true\n"
    "Name[en_US]=Workrave\n"
    "Name=Workrave\n"
    "Comment[en_US]=\n"
    "Comment=\n"
)

# dconf key (relative to /org/workrave) -> literal value exactly as `dconf write` expects it.
DCONF_SETTINGS: dict[str, str] = {
    "timers/micro-pause/auto-reset": "10",
    "timers/rest-break/limit": "1500",
    "timers/rest-break/auto-reset": "300",
    "timers/daily-limit/limit": "21600",
    "sound/events/break-ignored-enabled": "false",
    "sound/events/break-prelude-enabled": "false",
    "sound/events/exercise-ended-enabled": "false",
    "sound/events/exercises-ended-enabled": "false",
    "sound/events/exercise-step-enabled": "false",
    "sound/events/micro-break-ended-enabled": "false",
    "sound/events/micro-break-started-enabled": "false",
    "sound/events/rest-break-started-enabled": "false",
    "gui/breaks/block-mode": "0",
}

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
        name="Create Workrave autostart entry",
        src=StringIO(AUTOSTART_DESKTOP_ENTRY),
        dest=f"/home/{username}/.config/autostart/workrave.desktop",
        user=username,
        group=username,
        mode="644",
        _sudo=False,
    )

def _configure_dconf(username: str):
    uid = resolve_uid(username)
    if not uid:
        host.noop("could not resolve uid - skipping Workrave dconf settings")
        return

    env = get_dbus_env(uid)
    commands: list[str] = []
    for key, value in DCONF_SETTINGS.items():
        path = f"/org/workrave/{key}"
        current = host.get_fact( # pyright: ignore[reportUnknownMemberType]
            Command,
            command=f"{env} dconf read {path} 2>/dev/null || true",
            _sudo_user=username,
        )
        if current and current.strip() == value:
            continue
        commands.append(f"{env} dconf write {path} {value}")

    if not commands:
        host.noop("Workrave dconf settings already applied")
        return

    server.shell(
        name="Apply Workrave dconf settings",
        commands=commands,
        _sudo_user=username,
    )

@deploy("Install Workrave")
def deploy_workrave():
    username = host.data.username
    pkgmgr.install(name="Install Workrave", packages=["workrave"])
    _install_autostart_entry(username)
    _configure_dconf(username)

deploy_workrave()
