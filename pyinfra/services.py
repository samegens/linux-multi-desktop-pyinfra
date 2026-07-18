"""Service name resolution - systemd unit names sometimes differ by package manager
(e.g. ssh/sshd). Add new Service members here as new services need distro-aware names;
everything else in the codebase should call service_name(), never hardcode a unit name.
"""

from enum import Enum

from pkgmgr import PackageManager, package_manager


class Service(Enum):
    SSH = "ssh"


SERVICE_NAMES: dict[PackageManager, dict[Service, str]] = {
    PackageManager.APT: {Service.SSH: "ssh"},
    PackageManager.DNF: {Service.SSH: "sshd"},
}


def service_name(service: Service) -> str:
    return SERVICE_NAMES[package_manager()][service]
