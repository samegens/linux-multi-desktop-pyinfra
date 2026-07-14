"""Locale, base dirs, apt packages, flatpak+flathub."""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, flatpak, server


@deploy("Base system setup")
def deploy_base():
    # /etc/default/locale is a symlink to ../locale.conf on this (systemd-style) layout,
    # not a plain file like on Fedora. files.put only compares content against regular
    # files - against a symlink it always takes the unconditional-overwrite path, which
    # would silently replace the symlink with a plain file every run. Write the real
    # underlying file instead and leave the symlink alone.
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
        dest="/etc/locale.conf",
        mode="644",
    )
    existing_locales = host.get_fact(Command, command="locale -a")
    if "en_US.utf8" in existing_locales:
        host.noop("en_US.UTF-8 locale is already generated")
    else:
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

    # No dedicated pyinfra flatpak-remote operation, so check + shell out instead.
    existing_remotes = host.get_fact(Command, command="flatpak remote-list --columns=name")
    if "flathub" in existing_remotes.split():
        host.noop("Flathub remote is already configured")
    else:
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
