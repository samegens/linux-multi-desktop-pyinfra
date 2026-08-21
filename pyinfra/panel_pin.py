"""Pin an application's launcher to the desktop panel/taskbar.

Dispatches on DesktopEnvironment (see desktop_env.py).
"""

import re
from typing import assert_never

from pyinfra.context import host
from pyinfra.facts.server import Command
from pyinfra.operations import server

from desktop_env import DesktopEnvironment, get_desktop_environment

KDE_APPLETSRC = "plasma-org.kde.plasma.desktop-appletsrc"

# Matches a "[Containments][N][Applets][M][Configuration][General]" group header immediately
# followed by its "launchers=" line - printed together by _read_kde_taskmanager's awk script.
_KDE_TASKMANAGER_GROUP = re.compile(
    r"^\[Containments\]\[(\d+)\]\[Applets\]\[(\d+)\]\[Configuration\]\[General\]$"
)

def _read_kde_taskmanager(config_path: str) -> tuple[str, str, list[str]] | None:
    """Finds the Task Manager applet's config group in `config_path` - identified as whichever
    "[Containments][N][Applets][M][Configuration][General]" group already has a launchers=
    line, since N/M are assigned by Plasma and vary per install. Returns (containment_id,
    applet_id, current launcher list), or None if no such group exists (no Task Manager panel
    widget present to pin to)."""
    output = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            "awk '/^\\[Containments\\]\\[[0-9]+\\]\\[Applets\\]\\[[0-9]+\\]"
            "\\[Configuration\\]\\[General\\]$/{grp=$0} "
            f"/^launchers=/{{print grp; print $0}}' {config_path}"
        ),
    )
    if not output:
        return None

    lines = output.splitlines()
    match = _KDE_TASKMANAGER_GROUP.match(lines[0])
    if not match or len(lines) < 2:
        return None

    containment_id, applet_id = match.group(1), match.group(2)
    launchers = lines[1].removeprefix("launchers=")
    return containment_id, applet_id, [l for l in launchers.split(",") if l]

def _pin_kde(desktop_file_id: str, username: str):
    config_path = f"/home/{username}/.config/{KDE_APPLETSRC}"
    launcher = f"applications:{desktop_file_id}"

    taskmanager = _read_kde_taskmanager(config_path)
    if taskmanager is None:
        host.noop(f"No Task Manager panel widget found in {config_path}, can't pin {desktop_file_id}")
        return

    containment_id, applet_id, launchers = taskmanager
    if launcher in launchers:
        host.noop(f"{desktop_file_id} is already pinned to the KDE Plasma panel")
        return

    new_value = ",".join([*launchers, launcher])
    server.shell( # pyright: ignore[reportUnknownMemberType]
        name=f"Pin {desktop_file_id} to the KDE Plasma panel",
        commands=[
            f"kwriteconfig6 --file {config_path} "
            f"--group Containments --group {containment_id} "
            f"--group Applets --group {applet_id} "
            f"--group Configuration --group General "
            f"--key launchers '{new_value}'",
            # Task Manager only picks up config file changes on (re)start - kquitapp6 exits
            # it, plasmashell's own watchdog/session restores it. Backgrounded so the shell
            # command returns immediately rather than waiting on the relaunched process.
            "kquitapp6 plasmashell; (plasmashell > /dev/null 2>&1 &)",
        ],
        _sudo=False,
    )

def _find_cinnamon_taskbar_settings_file(username: str) -> str | None:
    """The grouped-window-list applet (Cinnamon's taskbar) keeps its own pinned-apps list in
    its per-instance xlet settings file, not in any gsettings/dconf key - org.cinnamon
    favorite-apps is a wholly separate "Favorites" applet (a small quick-launch icon among the
    systray icons), confirmed live against mint_vm: pinning Firefox to the actual taskbar left
    favorite-apps untouched. Assumes a single grouped-window-list instance, true for every
    target here."""
    path = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            f"ls -1 /home/{username}/.config/cinnamon/spices/"
            "grouped-window-list@cinnamon.org/*.json 2>/dev/null | head -1"
        ),
        _sudo=False,
    )
    return path or None

def _read_cinnamon_pinned_apps(settings_file: str) -> list[str]:
    output = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            "python3 -c \"import json; "
            f"print('\\n'.join(json.load(open('{settings_file}'))['pinned-apps']['value']))\""
        ),
        _sudo=False,
    )
    return output.splitlines() if output else []

def _pin_cinnamon(desktop_file_id: str, username: str):
    settings_file = _find_cinnamon_taskbar_settings_file(username)
    if settings_file is None:
        host.noop(f"No grouped-window-list taskbar widget found for {username}, can't pin {desktop_file_id}")
        return

    if desktop_file_id in _read_cinnamon_pinned_apps(settings_file):
        host.noop(f"{desktop_file_id} is already pinned to the Cinnamon taskbar")
        return

    server.shell( # pyright: ignore[reportUnknownMemberType]
        name=f"Pin {desktop_file_id} to the Cinnamon taskbar",
        commands=[
            "python3 -c \"import json; "
            f"path = '{settings_file}'; "
            "data = json.load(open(path)); "
            f"data['pinned-apps']['value'].append('{desktop_file_id}'); "
            "json.dump(data, open(path, 'w'), indent=2)\"",
            # grouped-window-list only picks up its settings file on (re)start, same as KDE's
            # Task Manager above.
            "(cinnamon --replace > /dev/null 2>&1 &)",
        ],
        _sudo=False,
    )

def pin_to_panel(desktop_file_id: str, username: str):
    """Pins `desktop_file_id` (e.g. "com.mitchellh.ghostty.desktop") to the panel/taskbar."""
    desktop_environment = get_desktop_environment()
    match desktop_environment:
        case DesktopEnvironment.KDE_PLASMA:
            _pin_kde(desktop_file_id, username)
        case DesktopEnvironment.CINNAMON:
            _pin_cinnamon(desktop_file_id, username)
        case _:
            assert_never(desktop_environment)
