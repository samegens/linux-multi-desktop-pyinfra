"""Custom pyinfra operation for downloading + extracting a .tar.gz/.tar.xz/.zip archive as a
single atomic step. Not distro-specific (no PackageManager/Distro dispatch here) - a generic
helper for any module that installs a binary (or, for .zip, an arbitrary tree) from a GitHub-release-style archive.
"""

from typing import Generator

from pyinfra.context import host
from pyinfra.api.command import QuoteString, StringCommand
from pyinfra.api.operation import operation # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.facts.server import Command
from pyinfra.operations import files

# Each extension's extract command up to (but not including) the archive path itself - the
# archive path and destination flag/path are appended by _extract_command() below, since tar's
# "-C dest" and unzip's "-d dest" put the destination flag in different places relative to the
# archive argument.
EXTRACT_COMMANDS = {
    ".tgz": ["tar", "-xzf"],
    ".tar.gz": ["tar", "-xzf"],
    ".tar.xz": ["tar", "-xJf"],
    ".zip": ["unzip", "-oq"],
}

def _extract_command(url: str, archive: str, dest: str) -> StringCommand:
    for suffix, command in EXTRACT_COMMANDS.items():
        if url.endswith(suffix):
            dest_flag = "-d" if command[0] == "unzip" else "-C"
            return StringCommand(*command, QuoteString(archive), dest_flag, QuoteString(dest))
    raise ValueError(f"Unsupported archive extension in url {url!r} - add it to EXTRACT_COMMANDS")

def _download_and_extract_archive(
    url: str, dest: str, user: str | None = None, group: str | None = None
) -> Generator[StringCommand, None, None]:
    """Shared tail end of download_and_extract()/download_and_extract_latest_release() -
    downloads `url` to a temp file and extracts into `dest` (created if needed). `user`/`group`
    chown the tree afterwards, for a per-user install."""
    archive = host.get_temp_filename(url)
    yield from files.download._inner(src=url, dest=archive) # pyright: ignore[reportPrivateUsage, reportUnknownMemberType]
    yield StringCommand("mkdir", "-p", QuoteString(dest))
    yield _extract_command(url, archive, dest)
    if user or group:
        yield StringCommand("chown", "-R", f"{user or ''}:{group or ''}", QuoteString(dest))
    yield StringCommand("rm", "-f", QuoteString(archive))

@operation()
def download_and_extract(
    url: str, dest: str, creates: str, user: str | None = None, group: str | None = None
) -> Generator[StringCommand, None, None]:
    """Download `url` and extract into `dest` (created if needed) as one atomic operation,
    skipping if `creates` already exists. Avoids files.unarchive's preview-mode break when
    chained after files.download (confirmed live: broke Helm/k9s, then TagUI).

    `creates` must be a specific *regular file*, not a directory. Install the extracted binary onto
    PATH via files.link, not files.copy - files.copy would reintroduce the same preview-mode
    problem this operation exists to avoid.
    """
    if host.get_fact(File, path=creates): # pyright: ignore[reportUnknownMemberType]
        host.noop(f"{creates} already exists")
        return

    yield from _download_and_extract_archive(url, dest, user=user, group=group)

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

    yield from _download_and_extract_archive(tarball_url_template.format(version=latest_version), dest)
