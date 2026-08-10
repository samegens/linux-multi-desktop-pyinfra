"""Claude Code CLI."""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
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

    if host.get_fact(File, path=binary): # pyright: ignore[reportUnknownMemberType]
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

@deploy("Install Claude Code")
def deploy_claude_code():
    _remove_legacy_npm_install()
    _install_claude_code(host.data.username)

deploy_claude_code()
