"""System config-file path resolution - some paths differ by package manager (e.g. the
systemwide interactive bashrc, baked into the bash package as built for a given repository
ecosystem - see pkgmgr.py's module docstring). Add new SystemPath members here as new paths
need distro-aware resolution; everything else in the codebase should call
get_system_path(), never hardcode a path that's known to diverge.
"""

from enum import Enum

from pkgmgr import PackageManager, get_package_manager


class SystemPath(Enum):
    SYSTEM_BASHRC = "system_bashrc"


SYSTEM_PATHS: dict[PackageManager, dict[SystemPath, str]] = {
    PackageManager.APT: {SystemPath.SYSTEM_BASHRC: "/etc/bash.bashrc"},
    PackageManager.DNF: {SystemPath.SYSTEM_BASHRC: "/etc/bashrc"},
}


def get_system_path(path: SystemPath) -> str:
    return SYSTEM_PATHS[get_package_manager()][path]
