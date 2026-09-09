"""Jujutsu (jj) - Git-compatible version control system.

Also configures jj's own user.name/user.email (reusing the same group_data identity as
git.py) every run regardless of whether the binary itself was just installed, since jj
otherwise silently commits under an empty identity. Also sets ui.default-command so a
bare `jj` invocation doesn't print a hint.
"""

import shlex

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

from archives import download_and_extract
from github import latest_release_tag

JJ_BINARY_PATH = "/usr/local/bin/jj"

def _install_jj_binary():
    already_installed = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="command -v jj || true"
    )
    if already_installed:
        host.noop("jj is already installed")
        return

    version = latest_release_tag("jj-vcs/jj").lstrip("v")
    install_dir = f"/opt/jj-{version}"
    binary = f"{install_dir}/jj"

    download_and_extract(
        name="Download and extract Jujutsu",
        url=(
            "https://github.com/jj-vcs/jj/releases/download/"
            f"v{version}/jj-v{version}-x86_64-unknown-linux-musl.tar.gz"
        ),
        dest=install_dir,
        creates=binary,
    )
    files.link(
        name="Link jj binary into /usr/local/bin",
        path=JJ_BINARY_PATH,
        target=binary,
    )

def _configure_jj_settings(username: str):
    config: dict[str, str] = {
        "user.name": host.data.git_user_name,
        "user.email": host.data.git_user_email,
        # avoid the "Hint: use `jj -h`..." nag on a bare `jj` invocation.
        "ui.default-command": "log",
    }
    for key, value in config.items():
        # jj config get exits 1 with nothing useful on stdout when the key isn't set yet - the
        # `|| true` just keeps the fact from erroring out in that case, same as this repo's
        # other "tolerate a missing/unset value" Command facts.
        current = host.get_fact( # pyright: ignore[reportUnknownMemberType]
            Command, command=f"jj config get {key} 2>/dev/null || true", _sudo_user=username
        )
        if current and current.strip() == value:
            host.noop(f"jj {key} is already set to {value!r}")
            continue

        # jj config set --user creates ~/.config/jj/config.toml (and the directory) itself if
        # neither exists yet - confirmed live, no separate files.directory step needed.
        server.shell(
            name=f"Set jj {key}",
            commands=[f"jj config set --user {key} {shlex.quote(value)}"],
            _sudo_user=username,
        )

@deploy("Install Jujutsu")
def deploy_jj():
    _install_jj_binary()
    _configure_jj_settings(host.data.username)

deploy_jj()
