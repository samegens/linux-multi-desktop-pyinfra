"""Package-manager dispatch (apt/dnf) and the Distro -> PackageManager mapping. This is the
only file that should ever switch on Distro directly - everything else (here, in
services.py, in paths.py) switches on PackageManager instead, so adding a new apt- or
dnf-based distro is a one-line addition to DISTRO_PACKAGE_MANAGERS and OS_RELEASE_ID_TO_DISTRO
and nothing else.

PackageManager here means "repository/packaging ecosystem" (Debian's apt archives vs
Fedora/RHEL's dnf/rpm archives), not literally "which CLI binary runs install" - package
names, systemd unit names, and packaged config-file paths (see services.py, paths.py) are
all baked into the specific package as built for a given archive, so any distro pulling from
the same archive family shares the same answer. That's why PackageManager is the right
dispatch key for all of them, not just installs.

Distro is autodetected via DistroFact (/etc/os-release's ID field), same pattern as
desktop_env.py's DesktopEnvironmentFact - no group_data var to keep in sync, and it works
whether or not the target distro was anticipated ahead of time (as long as its ID is in
OS_RELEASE_ID_TO_DISTRO). Fails loudly (ValueError) if the ID isn't recognized.

Not named distro.py: pyinfra itself depends on the third-party `distro` PyPI package, and a
local pyinfra/distro.py would shadow it for anything run from this directory - the same class
of pitfall documented in CLAUDE.md for why vault.py isn't named secrets.py.
"""

from enum import Enum
from typing import assert_never

from typing_extensions import override

from pyinfra.api.facts import FactBase
from pyinfra.context import host
from pyinfra.facts.server import Command
from pyinfra.operations import apt, dnf, server

class Distro(Enum):
    MINT = "mint"
    FEDORA = "fedora"
    UBUNTU = "ubuntu"

class PackageManager(Enum):
    APT = "apt"
    DNF = "dnf"

DISTRO_PACKAGE_MANAGERS: dict[Distro, PackageManager] = {
    Distro.MINT: PackageManager.APT,
    Distro.FEDORA: PackageManager.DNF,
    Distro.UBUNTU: PackageManager.APT,
}

# /etc/os-release's ID field -> Distro, for autodetection. A distro sharing an existing
# package manager (like Distro.UBUNTU) is a one-line addition here, same as
# DISTRO_PACKAGE_MANAGERS above - verify the actual ID with `grep ^ID= /etc/os-release` on the
# real host before adding, don't guess.
OS_RELEASE_ID_TO_DISTRO: dict[str, Distro] = {
    "linuxmint": Distro.MINT,
    "fedora": Distro.FEDORA,
    "ubuntu": Distro.UBUNTU,
}

# Only packages whose *name* differs (or doesn't exist) under a given package manager. Keyed
# by PackageManager, not Distro - a name divergence is a package-manager property (e.g. any
# dnf-based distro calls it the same thing), not a per-distro one. Verify with
# `dnf info <name>` / `apt-cache policy <name>` before adding an entry - don't guess.
PACKAGE_NAME_OVERRIDES: dict[PackageManager, dict[str, str]] = {
    PackageManager.DNF: {
        "fonts-powerline": "powerline-fonts",
        "smbclient": "samba-client",
        "imagemagick": "ImageMagick",
    },
}

# python3 -m venv needs python3-venv on apt (Debian splits it out of the base python3
# package, confirmed via prepare.sh's existing bootstrap). Fedora's python3 package bundles
# the venv module already (confirmed live: `python3 -m venv` works out of the box on a stock
# Fedora install), so only pip needs installing explicitly there.
VENV_PREREQUISITE_PACKAGES: dict[PackageManager, list[str]] = {
    PackageManager.APT: ["python3-venv", "python3-pip"],
    PackageManager.DNF: ["python3-pip"],
}

# apt's arch naming differs from uname's Arch fact - needed by any module building an apt repo
# line or .deb download URL itself (e.g. cinc_auditor.py, docker.py). dnf-side URLs use uname's
# own "x86_64"/"aarch64" directly, no mapping needed there.
DEB_ARCH_MAP: dict[str, str] = {
    "x86_64": "amd64",
    "aarch64": "arm64",
}

# Ubuntu codename -> numeric release, for apt-archive download URLs that are versioned
# numerically (e.g. downloads.cinc.sh) rather than by codename. Public/stable Ubuntu release
# data, not something that needs live verification per host - unlike PACKAGE_NAME_OVERRIDES.
UBUNTU_CODENAME_TO_RELEASE: dict[str, str] = {
    "resolute": "26.04",
    "noble": "24.04",
    "jammy": "22.04",
}

def get_ubuntu_codename() -> str:
    """The Ubuntu codename a host's apt archive actually matches - NOT the host's own codename.
    For Ubuntu itself that's its own codename; for a derivative like Mint it's UBUNTU_CODENAME
    from /etc/os-release, which can differ a lot from the derivative's own codename (confirmed
    live: Mint 22.3 "zena" reports UBUNTU_CODENAME=noble, i.e. Ubuntu 24.04)."""
    line = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            "grep -h '^UBUNTU_CODENAME=' /etc/os-release "
            "|| grep -h '^VERSION_CODENAME=' /etc/os-release"
        ),
    )
    codename = line.split("=", 1)[1].strip().strip('"') if line else None
    if not codename:
        raise ValueError(
            "Could not resolve an Ubuntu codename from /etc/os-release's "
            "UBUNTU_CODENAME/VERSION_CODENAME"
        )
    return codename

def get_ubuntu_release() -> str:
    """The Ubuntu release a host's apt archive actually matches - NOT the host's own version
    number."""
    codename = get_ubuntu_codename()
    if codename not in UBUNTU_CODENAME_TO_RELEASE:
        raise ValueError(
            f"Unknown Ubuntu codename {codename!r} - add it to UBUNTU_CODENAME_TO_RELEASE "
            "in pkgmgr.py"
        )
    return UBUNTU_CODENAME_TO_RELEASE[codename]

def resolve_distro_from_os_release(os_release_content: str) -> Distro | None:
    for line in os_release_content.splitlines():
        if line.startswith("ID="):
            distro_id = line.split("=", 1)[1].strip().strip('"')
            return OS_RELEASE_ID_TO_DISTRO.get(distro_id)
    return None

class DistroFact(FactBase[Distro | None]):
    """The host's distro, autodetected from /etc/os-release's ID field, or None if it doesn't
    match a known entry in OS_RELEASE_ID_TO_DISTRO."""

    @override
    def command(self) -> str:
        return "cat /etc/os-release"

    @override
    def process(self, output: list[str]) -> Distro | None:
        return resolve_distro_from_os_release("\n".join(output))

def get_distro() -> Distro:
    distro = host.get_fact(DistroFact) # pyright: ignore[reportUnknownMemberType]
    if distro is None:
        raise ValueError(
            f"{host.name}: /etc/os-release's ID wasn't recognized - add it to "
            "OS_RELEASE_ID_TO_DISTRO in pkgmgr.py"
        )
    return distro

def get_package_manager() -> PackageManager:
    return DISTRO_PACKAGE_MANAGERS[get_distro()]

def resolve_package_names(pm: PackageManager, packages: list[str]) -> list[str]:
    """Pure name-resolution logic, pulled out of install() so it's unit-testable without a
    live pyinfra host context (no host.data.distro, no apt/dnf operations involved)."""
    overrides = PACKAGE_NAME_OVERRIDES.get(pm, {})
    return [overrides.get(p, p) for p in packages]

def install(name: str, packages: list[str], present: bool = True):
    pm = get_package_manager()
    resolved = resolve_package_names(pm, packages)
    match pm:
        case PackageManager.APT:
            apt.packages(name=name, packages=resolved, present=present)
        case PackageManager.DNF:
            dnf.packages(name=name, packages=resolved, present=present)
        case _:
            assert_never(pm)

def get_venv_prerequisite_packages(pm: PackageManager) -> list[str]:
    """Pure lookup, pulled out of install_venv_prerequisites() so it's unit-testable without a
    live host context, same as resolve_package_names()."""
    return VENV_PREREQUISITE_PACKAGES[pm]

def install_venv_prerequisites(name: str):
    pm = get_package_manager()
    install(name=name, packages=get_venv_prerequisite_packages(pm))

def update_cache(name: str):
    """No-op under dnf - it refreshes stale metadata itself on every install, unlike apt
    which needs an explicit periodic `apt update`. IMPORTANT: dnf.update() (or
    dnf.packages(update=True)) is NOT the dnf analog of apt.update() - it runs a full
    `dnf update -y` system upgrade. Never wire that in here by "obvious" analogy - on
    localhost that would trigger an unintended full-system upgrade on a real machine."""
    pm = get_package_manager()
    match pm:
        case PackageManager.APT:
            apt.update(name=name, cache_time=3600)
        case PackageManager.DNF:
            host.noop("dnf refreshes its own metadata cache automatically")
        case _:
            assert_never(pm)

def get_en_us_locale_content() -> str:
    """Locale file content, matching each package manager's own native convention - Debian's
    tooling (locale-gen) expects the full LC_* block; Fedora's own localectl/anaconda
    convention is a single quoted LANG line. Both ultimately land in /etc/locale.conf -
    systemd's real locale file on both distros (Mint's traditional /etc/default/locale is
    just a symlink to it, see modules/base.py) - so only the content format needs to vary,
    not the destination. The only locale this repo manages is en_US.UTF-8 - not generalized
    to arbitrary locales since nothing here needs that yet."""
    pm = get_package_manager()
    match pm:
        case PackageManager.APT:
            return (
                "LANG=en_US.UTF-8\n"
                "LC_NUMERIC=en_US.UTF-8\n"
                "LC_TIME=en_US.UTF-8\n"
                "LC_MONETARY=en_US.UTF-8\n"
                "LC_PAPER=en_US.UTF-8\n"
                "LC_NAME=en_US.UTF-8\n"
                "LC_ADDRESS=en_US.UTF-8\n"
                "LC_TELEPHONE=en_US.UTF-8\n"
                "LC_MEASUREMENT=en_US.UTF-8\n"
                "LC_IDENTIFICATION=en_US.UTF-8\n"
            )
        case PackageManager.DNF:
            return 'LANG="en_US.UTF-8"\n'
        case _:
            assert_never(pm)

def ensure_en_us_locale(name: str):
    """The only locale this repo manages is en_US.UTF-8 (see modules/base.py) - not
    generalized to arbitrary locales since nothing here needs that yet.

    Checks the actual behavior first (locale -a) rather than a package-manager-specific
    proxy for it. Verified on a real Fedora machine: en_US.utf8 was already listed (and
    functional - `LANG=en_US.UTF-8 locale charmap` returned UTF-8 cleanly) with
    glibc-langpack-en not installed, so checking for that package instead of the actual
    locale would report a change that doesn't correspond to anything actually missing.
    Still correctly falls through to installing it on a genuinely fresh Fedora machine
    where the locale isn't already available.
    """
    existing_locales = host.get_fact(Command, command="locale -a") # pyright: ignore[reportUnknownMemberType]
    if existing_locales and "en_US.utf8" in existing_locales:
        host.noop("en_US.UTF-8 locale is already generated")
        return

    pm = get_package_manager()
    match pm:
        case PackageManager.DNF:
            install(name=name, packages=["glibc-langpack-en"])
        case PackageManager.APT:
            server.shell(name=name, commands=["locale-gen en_US.UTF-8"])
        case _:
            assert_never(pm)
