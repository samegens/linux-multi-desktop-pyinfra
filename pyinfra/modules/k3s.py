"""k3s (single-node Kubernetes) + Helm + k9s - the "developer/k3s-experiment-station" goal.
Ported from fedora-desktop's ansible/tasks/k3s.yml. Always installs whatever is currently latest
for all three, not a pinned version like starship_version/go_version/cinc_auditor_version
elsewhere in this repo - deliberate for this dev-experimentation tooling specifically, not a
general policy change (see memory: latest-version preference is scoped to k3s/Helm/k9s).

k3s's own install script (get.k3s.io) and the Helm/k9s GitHub release tarballs are self-contained
binaries with no apt/dnf packaging at all, so none of this branches on PackageManager except the
firewall trust rules for k3s's pod/service networks (routed through the firewall.py abstraction -
see its docstring for why: Fedora only has firewalld, Mint's remote VM has no firewalld at all).

Kubeconfig access: fedora-desktop's task adds the user to the "adm" group, but nothing in that
task actually sets /etc/rancher/k3s/k3s.yaml's group ownership to adm - checking a real box, it's
root:adm 640, apparently from undocumented prior setup, not the script itself. Not reproduced
here - instead passes K3S_KUBECONFIG_MODE=644 to the install script, k3s's own documented,
self-contained way to make the kubeconfig world-readable.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Arch, Command
from pyinfra.operations import files, server

import firewall
from archives import download_and_extract
from github import latest_release_tag

# k3s's default pod/service network CIDRs (Flannel backend) - not distro/host-specific.
K3S_TRUSTED_NETWORKS = ["10.42.0.0/16", "10.43.0.0/16"]

# Go-ecosystem release-arch naming (Helm, k9s) - same amd64/arm64 values as go.py's GO_ARCH_MAP,
# kept separate since the reason they match is coincidental (shared Go tooling convention, not a
# package-manager concept), not a case for reuse via pkgmgr.py.
RELEASE_ARCH_MAP = {
    "x86_64": "amd64",
    "aarch64": "arm64",
}

def _latest_k3s_version() -> str:
    """The install script itself resolves "latest stable" the same way when
    INSTALL_K3S_VERSION is unset - this mirrors that exact resolution so the idempotency check
    stays in sync with what the script would actually install. Uses a GET (curl -sL/-w), not
    HEAD (curl -I) - confirmed live that update.k3s.io returns 405 with no Location header for
    HEAD requests, which silently made this always resolve to "" and forced a reinstall attempt
    on every single run."""
    location = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            "curl -s -o /dev/null -w '%{redirect_url}' "
            "https://update.k3s.io/v1-release/channels/stable"
        ),
    )
    return location.rsplit("/", 1)[-1].strip() if location else ""

@deploy("Install k3s")
def deploy_k3s():
    latest_version = _latest_k3s_version()
    installed_version = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="k3s --version 2>/dev/null | head -1 || true"
    )

    if installed_version and latest_version and latest_version in installed_version:
        host.noop(f"k3s {latest_version} is already installed")
    else:
        files.download(
            name="Download k3s install script",
            src="https://get.k3s.io",
            dest="/tmp/k3s-install.sh",
            mode="755",
        )
        server.shell(
            name="Install k3s",
            commands=["/tmp/k3s-install.sh"],
            _env={"INSTALL_K3S_EXEC": "server", "K3S_KUBECONFIG_MODE": "644"},
        )

    server.service(name="Enable k3s service", service="k3s", running=True, enabled=True)

    for network in K3S_TRUSTED_NETWORKS:
        firewall.trust_source(name=f"Trust k3s network {network} in firewall", source=network)

@deploy("Install Helm")
def deploy_helm():
    version = latest_release_tag("helm/helm")
    installed = host.get_fact(Command, command="helm version --short 2>/dev/null || true") # pyright: ignore[reportUnknownMemberType]

    if installed and version and version in installed:
        host.noop(f"Helm {version} is already installed")
        return

    arch = RELEASE_ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
    extract_dir = f"/opt/helm-{version}"
    binary = f"{extract_dir}/linux-{arch}/helm"
    download_and_extract(
        name="Download and extract Helm",
        url=f"https://get.helm.sh/helm-{version}-linux-{arch}.tar.gz",
        dest=extract_dir,
        creates=binary,
    )
    files.link(
        name="Link Helm binary into /usr/local/bin",
        path="/usr/local/bin/helm",
        target=binary,
    )

@deploy("Install k9s")
def deploy_k9s():
    version = latest_release_tag("derailed/k9s")
    installed = host.get_fact(Command, command="k9s version --short 2>/dev/null || true") # pyright: ignore[reportUnknownMemberType]

    if installed and version and version in installed:
        host.noop(f"k9s {version} is already installed")
        return

    arch = RELEASE_ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
    extract_dir = f"/opt/k9s-{version}"
    binary = f"{extract_dir}/k9s"
    download_and_extract(
        name="Download and extract k9s",
        url=f"https://github.com/derailed/k9s/releases/download/{version}/k9s_Linux_{arch}.tar.gz",
        dest=extract_dir,
        creates=binary,
    )
    files.link(
        name="Link k9s binary into /usr/local/bin",
        path="/usr/local/bin/k9s",
        target=binary,
    )

deploy_k3s()
deploy_helm()
deploy_k9s()
