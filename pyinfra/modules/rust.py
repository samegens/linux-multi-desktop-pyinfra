"""Rust toolchain (rustup) - distro-agnostic, doesn't route through pkgmgr."""

from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

@deploy("Install Rust")
def deploy_rust():
    username = host.data.username
    cargo_bin = f"/home/{username}/.cargo/bin"

    is_installed = host.get_fact(
        Command,
        command=f"{cargo_bin}/rustc --version 2>/dev/null || true",
        _sudo_user=username,
    )

    if is_installed:
        host.noop("Rust is already installed")
    else:
        files.download(
            name="Download rustup installer",
            src="https://sh.rustup.rs",
            dest="/tmp/rustup-init.sh",
            mode="755",
        )
        server.shell(
            name="Install rustup and stable toolchain",
            commands=["/tmp/rustup-init.sh -y --default-toolchain stable"],
            _sudo_user=username,
        )
        files.file(
            name="Clean up rustup installer",
            path="/tmp/rustup-init.sh",
            present=False,
        )

deploy_rust()
