"""Docker Engine, installed from Docker's own official apt/dnf repo - not the distro's own
docker.io/moby-engine packages.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.facts.server import Arch, Command
from pyinfra.operations import apt, dnf, server

import pkgmgr
from pkgmgr import DEB_ARCH_MAP, PackageManager
from services import Service, get_service_name

DOCKER_PACKAGES = [
    "docker-ce",
    "docker-ce-cli",
    "containerd.io",
    "docker-buildx-plugin",
    "docker-compose-plugin",
]

# Unofficial/legacy packages that conflict with the official docker-ce packages above - per
# docs.docker.com's own "Uninstall old versions" step for each distro family.
OLD_DOCKER_PACKAGES: dict[PackageManager, list[str]] = {
    PackageManager.APT: [
        "docker.io",
        "docker-compose",
        "docker-compose-v2",
        "docker-doc",
        "podman-docker",
    ],
    PackageManager.DNF: [
        "docker",
        "docker-client",
        "docker-client-latest",
        "docker-common",
        "docker-latest",
        "docker-latest-logrotate",
        "docker-logrotate",
        "docker-selinux",
        "docker-engine-selinux",
        "docker-engine",
    ],
}

APT_KEYRING_PATH = "/etc/apt/keyrings/docker.gpg"

def _ensure_apt_repo():
    repo_file = "/etc/apt/sources.list.d/docker.list"
    if host.get_fact(File, path=repo_file): # pyright: ignore[reportUnknownMemberType]
        host.noop("Docker apt repo already configured")
        return

    apt.key(name="Add Docker apt GPG key", src="https://download.docker.com/linux/ubuntu/gpg", dest="docker.gpg")
    codename = pkgmgr.get_ubuntu_codename()
    arch = DEB_ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
    apt.repo(
        name="Add Docker apt repo",
        src=(
            f"deb [arch={arch} signed-by={APT_KEYRING_PATH}] "
            f"https://download.docker.com/linux/ubuntu {codename} stable"
        ),
        filename="docker",
    )
    # Force a real refresh - base.py already ran apt.update(cache_time=3600) earlier in the
    # full deploy, so the routine cached update wouldn't pick up this brand new source until
    # the cache_time window expires. Same fix as vscode.py's _ensure_apt_repo() - and same
    # guard above it, so this only runs the one time the repo is actually newly added.
    apt.update(name="Refresh apt cache for new Docker repo")

def _ensure_dnf_repo():
    dnf.repo(
        name="Add Docker dnf repo",
        src="https://download.docker.com/linux/fedora/docker-ce.repo",
    )

@deploy("Install Docker")
def deploy_docker():
    username = host.data.username
    pm = pkgmgr.get_package_manager()

    # Gated on Docker not already being installed, not just left to present=False's own
    # idempotency check - confirmed live on Fedora that dnf's virtual-Provides matching makes
    # the legacy name "docker" falsely match the already-installed docker-ce package (which
    # Provides: docker for compatibility), so it queues (harmless, no-op) removal commands on
    # every single run instead of detecting nothing needs removing. This cleanup only matters
    # before Docker itself is installed anyway.
    docker_installed = host.get_fact(Command, command="command -v docker || true") # pyright: ignore[reportUnknownMemberType]
    if docker_installed:
        host.noop("Docker already installed - skipping legacy-package cleanup")
    else:
        pkgmgr.install(
            name="Remove old/conflicting Docker packages",
            packages=OLD_DOCKER_PACKAGES[pm],
            present=False,
        )

    match pm:
        case PackageManager.APT:
            _ensure_apt_repo()
        case PackageManager.DNF:
            _ensure_dnf_repo()
        case _:
            assert_never(pm)

    pkgmgr.install(name="Install Docker Engine", packages=DOCKER_PACKAGES)

    server.service(
        name="Enable Docker service",
        service=get_service_name(Service.DOCKER),
        running=True,
        enabled=True,
    )

    server.user(
        name=f"Add {username} to the docker group",
        user=username,
        groups=["docker"],
        append=True,
    )

deploy_docker()
