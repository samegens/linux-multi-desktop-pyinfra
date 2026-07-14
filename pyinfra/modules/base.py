"""Locale, base dirs, apt packages, flatpak+flathub."""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import apt, files, flatpak, server


@deploy("Base system setup")
def deploy_base():
    files.put(
        name="Set locale",
        src=StringIO(
            "LANG=en_US.UTF-8\n"
            "LC_NUMERIC=en_US.UTF-8\n"
            "LC_TIME=en_US.UTF-8\n"
            "LC_MONETARY=en_US.UTF-8\n"
            "LC_PAPER=en_US.UTF-8\n"
            "LC_NAME=en_US.UTF-8\n"
            "LC_ADDRESS=en_US.UTF-8\n"
            "LC_TELEPHONE=en_US.UTF-8\n"
            "LC_MEASUREMENT=en_US.UTF-8\n"
            "LC_IDENTIFICATION=en_US.UTF-8\n"
        ),
        dest="/etc/default/locale",
        mode="644",
    )
    server.shell(
        name="Generate en_US.UTF-8 locale",
        commands=["locale-gen en_US.UTF-8"],
    )

    for path in [".config", ".config/autostart", "apps", ".local", ".local/share",
                 ".local/share/applications", ".local/share/icons"]:
        files.directory(
            name=f"Create ~/{path}",
            path=f"/home/{host.data.username}/{path}",
            user=host.data.username,
            group=host.data.username,
            mode="700" if path == ".config" else "775",
            _sudo=False,
        )

    apt.update(name="Update apt cache", cache_time=3600)
    apt.packages(
        name="Install base packages",
        packages=host.data.apt_packages,
        present=True,
    )

    # No dedicated pyinfra flatpak-remote operation; --if-not-exists keeps this safe to
    # rerun even though pyinfra can't detect no-op state for a raw shell command.
    server.shell(
        name="Add Flathub remote",
        commands=[
            "flatpak remote-add --if-not-exists flathub "
            "https://flathub.org/repo/flathub.flatpakrepo"
        ],
    )
    flatpak.packages(
        name="Install flatpaks",
        packages=host.data.flatpaks,
        remote="flathub",
        present=True,
    )


deploy_base()
