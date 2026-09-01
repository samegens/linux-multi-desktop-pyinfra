"""Betterbird - Thunderbird fork, email client. Package itself (eu.betterbird.Betterbird) is
installed by base.py via host.data.flatpaks; this module pins it to the panel and forces
ISO 8601 (yyyy-MM-dd) date formatting.

The date override is written as user.js into every existing flatpak profile directory. Flatpak
profile dirs get a random-salt name (e.g. "ar19wypd.default-default") assigned on first launch,
so there's no deterministic path to target - profiles are instead discovered by which
subdirectories of .thunderbird contain a prefs.js. user.js is merged over prefs.js on every
launch regardless of profile name, so this survives Betterbird rewriting prefs.js. On a host
where Betterbird has never been launched, no profile exists yet and this is a no-op until one
does.
"""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files

from panel_pin import pin_to_panel

BETTERBIRD_DESKTOP_FILE_ID = "eu.betterbird.Betterbird.desktop"
PROFILES_DIR = ".var/app/eu.betterbird.Betterbird/.thunderbird"

DATE_FORMAT_PREFS = {
    "intl.date_time.pattern_override.date_short": "yyyy-MM-dd",
    "intl.date_time.pattern_override.date_medium": "yyyy-MM-dd",
    "intl.date_time.pattern_override.date_long": "yyyy-MM-dd",
    "intl.date_time.pattern_override.date_full": "yyyy-MM-dd",
}

def _user_js_content() -> str:
    return "".join(f'user_pref("{key}", "{value}");\n' for key, value in DATE_FORMAT_PREFS.items())

def _profile_dirs(username: str) -> list[str]:
    thunderbird_dir = f"/home/{username}/{PROFILES_DIR}"
    result = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            f"find {thunderbird_dir} -mindepth 1 -maxdepth 1 -type d "
            "-exec test -e '{}/prefs.js' \\; -print 2>/dev/null || true"
        ),
    )
    if not result:
        return []
    return result.strip().splitlines()

@deploy("Pin Betterbird to panel")
def pin_betterbird_to_panel():
    pin_to_panel(BETTERBIRD_DESKTOP_FILE_ID, host.data.username)

@deploy("Force ISO 8601 date formatting in Betterbird")
def configure_betterbird_date_format():
    username = host.data.username
    profile_dirs = _profile_dirs(username)
    if not profile_dirs:
        host.noop("No Betterbird profile yet - date format override applies once one exists")
        return

    for profile_dir in profile_dirs:
        files.put(
            name=f"Force ISO 8601 dates in {profile_dir}",
            src=StringIO(_user_js_content()),
            dest=f"{profile_dir}/user.js",
            user=username,
            group=username,
            mode="644",
            _sudo=False,
        )

pin_betterbird_to_panel()
configure_betterbird_date_format()
