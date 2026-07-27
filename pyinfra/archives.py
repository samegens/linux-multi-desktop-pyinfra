"""Custom pyinfra operation for downloading + extracting a .tar.gz archive as a single atomic
step. Not distro-specific (no PackageManager/Distro dispatch here) - a generic helper for any
module that installs a binary from a GitHub-release-style tarball (currently modules/k3s.py's
Helm and k9s installs).
"""

from typing import Generator

from pyinfra.context import host
from pyinfra.api.command import QuoteString, StringCommand
from pyinfra.api.operation import operation # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.operations import files

@operation()
def download_and_extract(url: str, dest: str, creates: str) -> Generator[StringCommand, None, None]:
    """Download a .tar.gz `url` and extract its full contents into `dest` (created if needed),
    as a single atomic operation, skipping entirely if `creates` already exists.

    `creates` must be a specific expected file, not just `dest` itself - checking `dest` alone
    breaks if it's a directory that already exists for unrelated reasons (e.g. /usr/share),
    which would false-positive-skip forever. Checked against *pre-existing* state (safe in
    preview/no -y mode), same idea as files.unarchive's own `creates=`.

    Not files.download + files.unarchive as two separate operations: files.unarchive checks its
    source archive exists via host.get_fact(File, ...) at operation-definition time, which fails
    when chained directly after a files.download in the same run - that download has only been
    *queued* (not yet executed) at that point during a preview run. Confirmed live: this broke
    Helm/k9s's install on a fresh `--limit localhost` preview. Composed from files.download's own
    well-tested logic via `_inner()` - the same technique pyinfra's own apt.deb/dnf.rpm use to
    combine "download from URL" with a following step - plus raw tar commands via
    StringCommand/QuoteString (pyinfra's own primitives), since unarchive has no equivalent
    "download inline, don't pre-check" mode.

    The step that installs the extracted binary somewhere on PATH must use files.link, not
    files.copy - files.link only checks the fact of its own `path`, never `target`'s existence,
    so it's safe to chain right after this operation even in preview mode. files.copy checks its
    `src` exists the same way unarchive does, and would reintroduce the exact problem this
    operation exists to avoid.
    """
    if host.get_fact(File, path=creates): # pyright: ignore[reportUnknownMemberType]
        host.noop(f"{creates} already exists")
        return

    archive = host.get_temp_filename(url)
    yield from files.download._inner(src=url, dest=archive) # pyright: ignore[reportPrivateUsage, reportUnknownMemberType]
    yield StringCommand("mkdir", "-p", QuoteString(dest))
    yield StringCommand("tar", "-xzf", QuoteString(archive), "-C", QuoteString(dest))
    yield StringCommand("rm", "-f", QuoteString(archive))
