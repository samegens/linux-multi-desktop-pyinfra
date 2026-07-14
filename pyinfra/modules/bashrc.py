"""~/.bashrc and ~/.inputrc. Trimmed to what lean-core actually installs (Rust, Docker) -
add lines back here as deferred modules (k3s, SSH host aliases, ...) get ported."""

from io import StringIO

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.operations import files


@deploy("Configure dotfiles")
def deploy_bashrc():
    username = host.data.username
    bashrc = f"/home/{username}/.bashrc"

    files.line(
        name="Add Cargo bin to PATH",
        path=bashrc,
        line='export PATH="$HOME/.cargo/bin:$PATH"',
        _sudo=False,
    )

    aliases = {
        "ll": "alias ll='ls -alF'",
        "pandoc": "alias pandoc='docker run --rm -v \"$(pwd):/data\" -u $(id -u):$(id -g) pandoc/latex'",
        "sizeof": "alias sizeof='du -sh'",
        "ds": 'ds() { if [ -z "$1" ]; then echo "Usage: ds <docker-image>"; return 1; fi; '
        'docker run --rm -it -v "$(pwd):/data" "$1" /bin/bash; }',
    }
    for alias_name, line in aliases.items():
        files.line(
            name=f"Add alias: {alias_name}",
            path=bashrc,
            line=line,
            _sudo=False,
        )

    files.put(
        name="Create .inputrc",
        src=StringIO(
            "set completion-ignore-case On\n"
            "# ctrl-backspace removes previous word:\n"
            '"\\C-h": backward-kill-word\n'
            "# ctrl-delete removes current word:\n"
            '"\\e[3;5~": kill-word\n'
        ),
        dest=f"/home/{username}/.inputrc",
        user=username,
        group=username,
        mode="644",
        _sudo=False,
    )
