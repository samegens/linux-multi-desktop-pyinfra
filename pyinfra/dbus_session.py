"""Resolves a real per-user D-Bus session bus for modules that shell out to
gsettings/dconf as a target user. `sudo -u`/`_sudo_user` alone gives a bare shell with no
XDG_RUNTIME_DIR/DBUS_SESSION_BUS_ADDRESS, so those tools can't find the user's real bus at
/run/user/<uid>/bus and silently talk to a disposable one instead - writes appear to succeed
but vanish. Pointing at the real bus explicitly means a missing session now fails/returns
nothing instead of silently no-opping against a fake one. Shared by modules/vscode.py and
modules/workrave.py.
"""

from pyinfra.context import host
from pyinfra.facts.server import Command

def resolve_uid(username: str) -> str | None:
    uid = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=f"id -u {username} 2>/dev/null || true",
        _sudo_user=username,
    )
    return uid.strip() if uid else None

def get_dbus_env(uid: str) -> str:
    return f"XDG_RUNTIME_DIR=/run/user/{uid} DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus"
