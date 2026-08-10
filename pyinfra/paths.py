"""System path constants and resolution."""

from enum import Enum

from pkgmgr import PackageManager, get_package_manager

# Created by modules/base.py. Used by any module that downloads a versioned package artifact
# (.deb/.rpm/install script) to a location that survives a reboot, unlike pyinfra's own
# managed /tmp temp files - see modules/cinc_auditor.py's _download_cinc_auditor_package()
# docstring for why that distinction matters.
PYINFRA_CACHE_DIR = "/var/cache/pyinfra"


class SystemPath(Enum):
    SYSTEM_BASHRC = "system_bashrc"


SYSTEM_PATHS: dict[PackageManager, dict[SystemPath, str]] = {
    PackageManager.APT: {SystemPath.SYSTEM_BASHRC: "/etc/bash.bashrc"},
    PackageManager.DNF: {SystemPath.SYSTEM_BASHRC: "/etc/bashrc"},
}


def get_system_path(path: SystemPath) -> str:
    return SYSTEM_PATHS[get_package_manager()][path]
