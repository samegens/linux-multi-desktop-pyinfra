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
            # command returns immediately rather than waiting on the relaunched process. Only
            # reached for @local targets (this repo's only KDE target is localhost) so
            # DISPLAY/XAUTHORITY are already the real session's - unlike the Cinnamon case
            # below, which is always a remote SSH target.
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

def _is_flatpak_app(desktop_file_id: str) -> bool:
    # Checked against host.data.flatpaks (the same list base.py installs from) rather than
    # shelling out to `flatpak info` - pyinfra builds the whole operation graph in a single
    # pass, so any host.get_fact() here runs against pre-deploy remote state, before base.py's
    # flatpak.packages() op has actually installed anything. Confirmed live against
    # dell_laptop: on a fresh install, that live check always reported "not installed yet"
    # and Obsidian/BetterBird got pinned in bare form - see the ":flatpak" comment below.
    app_id = desktop_file_id.removesuffix(".desktop")
    return app_id in host.data.flatpaks

def _pin_cinnamon(desktop_file_id: str, username: str):
    # grouped-window-list needs a ":flatpak" suffix on the desktop-file-id to resolve a
    # Flatpak app's windows/icon - confirmed live against mint_vm: Cinnamon's own "Pin to
    # panel" UI wrote "md.obsidian.Obsidian.desktop:flatpak", not the bare id; the bare form
    # never rendered on the taskbar even though the file, the pinned-apps list, and
    # Gio.DesktopAppInfo resolution were all otherwise correct. Native (non-Flatpak) apps use
    # the bare id, same as KDE's launchers= below.
    is_flatpak = _is_flatpak_app(desktop_file_id)
    launcher = f"{desktop_file_id}:flatpak" if is_flatpak else desktop_file_id
    stale_launcher = desktop_file_id if is_flatpak else f"{desktop_file_id}:flatpak"

    settings_file = _find_cinnamon_taskbar_settings_file(username)
    if settings_file is None:
        host.noop(f"No grouped-window-list taskbar widget found for {username}, can't pin {desktop_file_id}")
        return

    pinned = _read_cinnamon_pinned_apps(settings_file)
    if launcher in pinned:
        host.noop(f"{desktop_file_id} is already pinned to the Cinnamon taskbar")
        return

    # A previous run may have pinned the wrong form (e.g. bare id for a Flatpak app, written
    # before it was actually installed) - replace it in place rather than appending a
    # duplicate entry alongside it.
    if stale_launcher in pinned:
        script = (
            "import json; "
            f"path = '{settings_file}'; "
            "data = json.load(open(path)); "
            "apps = data['pinned-apps']['value']; "
            f"apps[apps.index('{stale_launcher}')] = '{launcher}'; "
            "json.dump(data, open(path, 'w'), indent=2)"
        )
        op_name = f"Fix {desktop_file_id}'s pinned Cinnamon taskbar entry"
    else:
        script = (
            "import json; "
            f"path = '{settings_file}'; "
            "data = json.load(open(path)); "
            f"data['pinned-apps']['value'].append('{launcher}'); "
            "json.dump(data, open(path, 'w'), indent=2)"
        )
        op_name = f"Pin {desktop_file_id} to the Cinnamon taskbar"

    # grouped-window-list only picks up this file on (re)start, but unlike KDE's plasmashell
    # restart above, restarting cinnamon isn't attempted here: this repo's only Cinnamon
    # target (mint_vm) is always reached over plain SSH, which has no DISPLAY/XAUTHORITY env -
    # confirmed live that `cinnamon --replace` then either no-ops ("Window manager warning:
    # Unsupported session type", old process never exits) or, once those vars are manually
    # forwarded from the running session's /proc/<pid>/environ, starts a genuinely new
    # instance that still doesn't evict the old one, leaving two competing shells fighting
    # over the same display until one is killed by hand. Writing the file and leaving the
    # live refresh to the next login/manual restart is the reliable option.
    server.shell( # pyright: ignore[reportUnknownMemberType]
        name=op_name,
        commands=[f'python3 -c "{script}"'],
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
