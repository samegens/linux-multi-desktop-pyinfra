"""Package-manager dispatch (apt/dnf) and the Distro -> PackageManager mapping. This is the
only file that should ever switch on Distro directly - everything else (here, in
services.py, in paths.py) switches on PackageManager instead, so adding a new apt- or
dnf-based distro is a one-line addition to DISTRO_PACKAGE_MANAGERS and nothing else.

PackageManager here means "repository/packaging ecosystem" (Debian's apt archives vs
Fedora/RHEL's dnf/rpm archives), not literally "which CLI binary runs install" - package
names, systemd unit names, and packaged config-file paths (see services.py, paths.py) are
all baked into the specific package as built for a given archive, so any distro pulling from
the same archive family shares the same answer. That's why PackageManager is the right
dispatch key for all of them, not just installs.

Not named distro.py: pyinfra itself depends on the third-party `distro` PyPI package, and a
local pyinfra/distro.py would shadow it for anything run from this directory - the same class
of pitfall documented in CLAUDE.md for why vault.py isn't named secrets.py.
"""

from enum import Enum
from typing import assert_never

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

def get_distro() -> Distro:
    configured_distro = host.data.distro
    if configured_distro is None:
        raise ValueError(
            "host.data.distro is unset - set it in pyinfra/group_data/<host>.py "
            "before deploying to this host"
        )
    return configured_distro

def get_package_manager() -> PackageManager:
    return DISTRO_PACKAGE_MANAGERS[get_distro()]

def resolve_package_names(pm: PackageManager, packages: list[str]) -> list[str]:
    """Pure name-resolution logic, pulled out of install() so it's unit-testable without a
    live pyinfra host context (no host.data.distro, no apt/dnf operations involved)."""
    overrides = PACKAGE_NAME_OVERRIDES.get(pm, {})
    return [overrides.get(p, p) for p in packages]

def install(name: str, packages: list[str]):
    pm = get_package_manager()
    resolved = resolve_package_names(pm, packages)
    match pm:
        case PackageManager.APT:
            apt.packages(name=name, packages=resolved, present=True)
        case PackageManager.DNF:
            dnf.packages(name=name, packages=resolved, present=True)
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
