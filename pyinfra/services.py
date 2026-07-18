"""Service name resolution - systemd unit names sometimes differ by package manager
(e.g. ssh/sshd, baked into the openssh-server package as built for a given repository
ecosystem - see pkgmgr.py's module docstring). Add new Service members here as new
services need distro-aware names; everything else in the codebase should call
get_service_name(), never hardcode a unit name.
"""

from enum import Enum

from pkgmgr import PackageManager, get_package_manager


class Service(Enum):
    SSH = "ssh"


SERVICE_NAMES: dict[PackageManager, dict[Service, str]] = {
    PackageManager.APT: {Service.SSH: "ssh"},
    PackageManager.DNF: {Service.SSH: "sshd"},
}


def get_service_name(service: Service) -> str:
    return SERVICE_NAMES[get_package_manager()][service]
