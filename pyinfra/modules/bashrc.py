"""~/.bashrc and ~/.inputrc. Trimmed to what lean-core actually installs (Rust, Docker) -
add lines back here as deferred modules (k3s, SSH host aliases, ...) get ported."""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files


@deploy("Configure dotfiles")
def deploy_bashrc():
    username = host.data.username
    bashrc = f"/home/{username}/.bashrc"

    # escape_regex_characters=True escapes ()/{}/etc assuming POSIX extended-regex
    # semantics (escaped = literal). The underlying grep defaults to basic-regex mode,
    # where \(  \)  \{  \} mean the *opposite* (grouping/interval operators) - so
    # escape_regex_characters=True is only correct when paired with extended_regex=True.
    # Without it, the presence-check never matches and the line gets re-added every run.
    files.line(
        name="Add Cargo bin to PATH",
        path=bashrc,
        line='export PATH="$HOME/.cargo/bin:$PATH"',
        escape_regex_characters=True,
        extended_regex=True,
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
            escape_regex_characters=True,
            extended_regex=True,
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


deploy_bashrc()
