"""Custom pyinfra operation for idempotently setting one `key=value` line in a flat,
non-sectioned key=value config file (e.g. darktable's darktablerc/shortcutsrc) - only the
line for `key` is touched, every other line in the file (including ones for other keys) is
left completely alone. Exists so a module can nudge a handful of settings in an otherwise
upstream-authored config file without adopting - and having to keep in sync with new
upstream releases of - the entire file via files.put/files.template.
"""

import re
from typing import Generator

from pyinfra.context import host
from pyinfra.api.command import QuoteString, StringCommand
from pyinfra.api.operation import operation # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import FindInFile

# FindInFile's own fact command runs plain `grep` (POSIX basic regex, no -E), and this
# operation's own replace command runs plain `sed` (same BRE mode) - both need `key` escaped
# the same way to be searched/replaced for literally rather than as a regex.
_BRE_SPECIAL_CHARACTERS = re.compile(r"[\\/.^$*\[\]]")
# sed's replacement side additionally treats & (whole match) specially - ^$.*[] have no
# meaning there, only \, / (the delimiter) and & need escaping.
_SED_REPLACEMENT_SPECIAL_CHARACTERS = re.compile(r"[\\/&]")

def _escape_for_sed_pattern(text: str) -> str:
    return _BRE_SPECIAL_CHARACTERS.sub(lambda m: f"\\{m.group(0)}", text)

def _escape_for_sed_replacement(text: str) -> str:
    return _SED_REPLACEMENT_SPECIAL_CHARACTERS.sub(lambda m: f"\\{m.group(0)}", text)

@operation()
def set_key_value(path: str, key: str, value: str) -> Generator[StringCommand, None, None]:
    """Ensures `path` contains exactly one `key=value` line for `key` - adding it (creating
    the file itself if needed, via shell `>>` - though its parent directory must already
    exist) if missing, correcting it in place if a differently-valued line for `key` is
    already there, and doing nothing if it's already correct. Every other line in the file
    is never touched.
    """
    match_pattern = f"^{_escape_for_sed_pattern(key)}="
    desired_line = f"{key}={value}"

    matching_lines = host.get_fact(FindInFile, path=path, pattern=match_pattern) # pyright: ignore[reportUnknownMemberType]

    if matching_lines == [desired_line]:
        host.noop(f"{key} in {path} is already set to {value!r}")
        return

    if matching_lines:
        sed_script = f"s/{match_pattern}.*/{_escape_for_sed_replacement(desired_line)}/"
        yield StringCommand("sed", "-i", QuoteString(sed_script), QuoteString(path))
    else:
        yield StringCommand("echo", QuoteString(desired_line), ">>", QuoteString(path))
