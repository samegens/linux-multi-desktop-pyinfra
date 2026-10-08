"""Claude Code CLI."""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File, Link
from pyinfra.facts.server import Command
from pyinfra.operations import files, npm, server

from paths import PYINFRA_CACHE_DIR

CLAUDE_INSTALL_SCRIPT = f"{PYINFRA_CACHE_DIR}/claude-install.sh"

def _remove_legacy_npm_install():
    npm_present = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="command -v npm || true"
    )
    if not npm_present:
        host.noop("npm not installed - nothing to clean up")
        return

    npm.packages(
        name="Remove legacy npm-installed Claude Code",
        packages=["@anthropic-ai/claude-code"],
        present=False,
        _sudo=False,
    )

def _install_claude_code(username: str):
    binary = f"/home/{username}/.local/bin/claude"

    if host.get_fact(File, path=binary) or host.get_fact(Link, path=binary): # pyright: ignore[reportUnknownMemberType]
        host.noop("Claude Code is already installed")
        return

    files.download(
        name="Download Claude Code installer",
        src="https://claude.ai/install.sh",
        dest=CLAUDE_INSTALL_SCRIPT,
        mode="755",
    )
    server.shell(
        name="Install Claude Code",
        commands=[CLAUDE_INSTALL_SCRIPT],
        _sudo=False,
    )

def _copy_config_files(username: str):
    config_dir = f"/home/{username}/.claude"

    files.directory(
        name="Create ~/.claude",
        path=config_dir,
        user=username,
        group=username,
        mode="755",
        _sudo=False,
    )

    for filename in ["settings.json", "CLAUDE.md"]:
        files.put(
            name=f"Copy Claude Code {filename}",
            src=f"files/claude/{filename}",
            dest=f"{config_dir}/{filename}",
            user=username,
            group=username,
            mode="644",
            _sudo=False,
        )

@deploy("Install Claude Code")
def deploy_claude_code():
    _remove_legacy_npm_install()
    _install_claude_code(host.data.username)
    _copy_config_files(host.data.username)

deploy_claude_code()
