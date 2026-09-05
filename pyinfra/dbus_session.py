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

def get_write_command_prefix(username: str) -> str:
    """Returns a shell command prefix that gives gsettings/dconf the user's real D-Bus session
    to write through - prepend directly to the real command, e.g. f"{prefix} dconf write ...".

    Requires the user's real per-user session bus (/run/user/<uid>/bus) to already be running -
    a write through a private `dbus-run-session` bus instead doesn't inform the real session's
    own dconf-service, which later re-serializes the database from its own in-memory state
    (e.g. on the next settings change, or on logout) and silently wipes the out-of-band write -
    confirmed live against dell_laptop, where such a write to a Cinnamon keybinding reverted
    after the next logout/login even though `dconf read` showed it correctly persisted right
    after the write. So a missing session bus (e.g. a host with no one logged in yet) is a
    deploy-ordering error, not something to silently paper over - fail loudly instead.
    """
    uid = resolve_uid(username)
    if not uid:
        raise ValueError(f"Could not resolve uid for {username} - can't find its D-Bus session")

    bus_exists = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=f"test -S /run/user/{uid}/bus && echo yes || true",
        _sudo_user=username,
    )
    if bus_exists != "yes":
        raise ValueError(
            f"No D-Bus session bus found at /run/user/{uid}/bus - {username} needs to be "
            "logged into a desktop session before this deploy step can run"
        )

    return get_dbus_env(uid)
