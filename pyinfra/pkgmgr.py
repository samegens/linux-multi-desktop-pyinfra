"""Package-manager dispatch (apt/dnf) and the Distro -> PackageManager mapping. This is the
only file that should ever switch on Distro directly - everything else (here and in
services.py) switches on PackageManager, so adding a new apt- or dnf-based distro is a
one-line addition to DISTRO_PACKAGE_MANAGERS and nothing else.

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
    PackageManager.DNF: {},
}


def package_manager() -> PackageManager:
    distro = host.data.distro
    if distro is None:
        raise ValueError(
            "host.data.distro is unset - set it in pyinfra/group_data/<host>.py "
            "before deploying to this host"
        )
    return DISTRO_PACKAGE_MANAGERS[distro]


def resolve_package_names(pm: PackageManager, packages: list[str]) -> list[str]:
    """Pure name-resolution logic, pulled out of install() so it's unit-testable without a
    live pyinfra host context (no host.data.distro, no apt/dnf operations involved)."""
    overrides = PACKAGE_NAME_OVERRIDES.get(pm, {})
    return [overrides.get(p, p) for p in packages]


def install(name: str, packages: list[str]):
    pm = package_manager()
    resolved = resolve_package_names(pm, packages)
    match pm:
        case PackageManager.APT:
            apt.packages(name=name, packages=resolved, present=True)
        case PackageManager.DNF:
            dnf.packages(name=name, packages=resolved, present=True)
        case _:
            assert_never(pm)


def update_cache(name: str):
    """No-op under dnf - it refreshes stale metadata itself on every install, unlike apt
    which needs an explicit periodic `apt update`. IMPORTANT: dnf.update() (or
    dnf.packages(update=True)) is NOT the dnf analog of apt.update() - it runs a full
    `dnf update -y` system upgrade. Never wire that in here by "obvious" analogy - on
    localhost that would trigger an unintended full-system upgrade on a real machine."""
    pm = package_manager()
    match pm:
        case PackageManager.APT:
            apt.update(name=name, cache_time=3600)
        case PackageManager.DNF:
            host.noop("dnf refreshes its own metadata cache automatically")
        case _:
            assert_never(pm)


def ensure_en_us_locale(name: str):
    """The only locale this repo manages is en_US.UTF-8 (see modules/base.py) - not
    generalized to arbitrary locales since nothing here needs that yet."""
    pm = package_manager()
    match pm:
        case PackageManager.DNF:
            # No locale-gen on Fedora - installing the langpack makes the locale
            # available directly; install()'s present=True check is already idempotent.
            install(name=name, packages=["glibc-langpack-en"])
        case PackageManager.APT:
            existing_locales = host.get_fact(Command, command="locale -a")
            if existing_locales and "en_US.utf8" in existing_locales:
                host.noop("en_US.UTF-8 locale is already generated")
            else:
                server.shell(name=name, commands=["locale-gen en_US.UTF-8"])
        case _:
            assert_never(pm)
