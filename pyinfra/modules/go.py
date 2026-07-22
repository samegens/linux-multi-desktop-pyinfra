"""Go toolchain."""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Arch, Command
from pyinfra.operations import files

from archives import download_and_extract

GO_ARCH_MAP = {
    "x86_64": "amd64",
    "aarch64": "arm64",
}

@deploy("Install Go")
def deploy_go():
    version = host.data.go_version
    # Command returns None (not "") when the command produces zero output lines,
    # which is the case here whenever /usr/local/go/bin/go doesn't exist yet.
    installed = host.get_fact(Command, command="/usr/local/go/bin/go version 2>/dev/null || true") # pyright: ignore[reportUnknownMemberType]

    if installed and f"go{version} " in installed:
        host.noop(f"Go {version} is already installed")
    else:
        files.directory(
            name="Remove existing Go installation (version mismatch)",
            path="/usr/local/go",
            present=False,
        )

        arch = GO_ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
        download_and_extract(
            name="Download and extract Go",
            url=f"https://go.dev/dl/go{version}.linux-{arch}.tar.gz",
            dest="/usr/local",
            creates="/usr/local/go/bin/go",
        )

    files.put(
        name="Add Go to PATH",
        src=StringIO("export PATH=$PATH:/usr/local/go/bin\n"),
        dest="/etc/profile.d/go.sh",
        mode="644",
    )

deploy_go()
