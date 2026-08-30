"""Custom pyinfra operation for downloading + extracting a .tar.gz/.tar.xz archive as a single
atomic step. Not distro-specific (no PackageManager/Distro dispatch here) - a generic helper for
any module that installs a binary from a GitHub-release-style tarball.
"""

from typing import Generator

from pyinfra.context import host
from pyinfra.api.command import QuoteString, StringCommand
from pyinfra.api.operation import operation # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.facts.server import Command
from pyinfra.operations import files

TAR_EXTRACT_FLAGS = {
    ".tgz": "-xzf",
    ".tar.gz": "-xzf",
    ".tar.xz": "-xJf",
}

def _get_tar_extract_flags(url: str) -> str:
    for suffix, flags in TAR_EXTRACT_FLAGS.items():
        if url.endswith(suffix):
            return flags
    raise ValueError(f"Unsupported archive extension in url {url!r} - add it to TAR_EXTRACT_FLAGS")

def _download_and_extract_tarball(url: str, dest: str) -> Generator[StringCommand, None, None]:
    """Shared tail end of both download_and_extract() and
    download_and_extract_latest_release() below - downloads `url` to a temp file and extracts
    it into `dest` (created if needed), unconditionally. Composed via files.download's own
    `_inner()` for the same reason download_and_extract's docstring explains: chaining a plain
    files.unarchive right after a files.download in the same run sees the download as merely
    *queued*, not yet executed, and fails its own pre-check.
    """
    tar_flags = _get_tar_extract_flags(url)
    archive = host.get_temp_filename(url)
    yield from files.download._inner(src=url, dest=archive) # pyright: ignore[reportPrivateUsage, reportUnknownMemberType]
    yield StringCommand("mkdir", "-p", QuoteString(dest))
    yield StringCommand("tar", tar_flags, QuoteString(archive), "-C", QuoteString(dest))
    yield StringCommand("rm", "-f", QuoteString(archive))

@operation()
def download_and_extract(url: str, dest: str, creates: str) -> Generator[StringCommand, None, None]:
    """Download a tarball from `url` and extract
    its full contents into `dest` (created if needed), as a single atomic operation, skipping
    entirely if file specified by `creates` already exists.

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

    yield from _download_and_extract_tarball(url, dest)

@operation()
def download_and_extract_latest_release(
    tag_api_url: str,
    tarball_url_template: str,
    dest: str,
    version_check_command: str,
) -> Generator[StringCommand, None, None]:
    """Like download_and_extract(), but for a tool that should always track the latest
    upstream release rather than a version pinned in group_data - re-resolves the latest tag on
    every run and only re-downloads when that differs from what's actually installed, instead of
    download_and_extract()'s one-shot `creates` check (which would never notice a new release
    once the binary first exists).

    `tarball_url_template` is the full download URL with a single `{version}` placeholder (arch
    already substituted by the caller, since that doesn't change run to run). `version_check_command`
    must print the installed binary's own version string somewhere in its output (e.g. `tool
    --version`) and is run tolerating a missing binary (`|| true`) - both gitleaks's and
    trufflehog's version output happen to already contain the bare X.Y.Z version, so a substring
    match against the resolved tag (stripped of its leading "v") is enough, no regex needed.
    """
    tag = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        # grep -oP pulls just the tag_name value regardless of whether GitHub's response is
        # pretty-printed (one JSON key per line) or compact (the whole payload on one line,
        # confirmed live for trufflehog's API response, unlike gitleaks's) - a plain
        # grep -m1 '"tag_name"' | cut -d'"' -f4 silently extracts the wrong field on the
        # compact-JSON case, since the matched "line" is then the entire payload.
        command=f"curl -fsSL {tag_api_url} | grep -m1 -oP '\"tag_name\"\\s*:\\s*\"\\K[^\"]+'",
    )
    if not tag:
        raise ValueError(f"Could not resolve the latest release tag from {tag_api_url}")
    latest_version = tag.strip().lstrip("v")

    installed_version_output = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=f"{version_check_command} 2>/dev/null || true",
    )
    if installed_version_output and latest_version in installed_version_output:
        host.noop(f"already at the latest version ({latest_version})")
        return

    yield from _download_and_extract_tarball(tarball_url_template.format(version=latest_version), dest)
