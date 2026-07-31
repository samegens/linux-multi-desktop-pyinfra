"""Locale, base dirs, apt packages, flatpak+flathub."""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Command
from pyinfra.operations import files, flatpak, server

import pkgmgr

@deploy("Base system setup")
def deploy_base():
    files.put(
        name="Set locale",
        src=StringIO(pkgmgr.get_en_us_locale_content()),
        dest="/etc/locale.conf",
        mode="644",
    )
    pkgmgr.ensure_en_us_locale(name="Ensure en_US.UTF-8 locale is available")

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

    files.directory(name="Create /var/cache/pyinfra", path="/var/cache/pyinfra")

    pkgmgr.update_cache(name="Update package cache")
    pkgmgr.install(name="Install base packages", packages=host.data.packages)

    pkgmgr.install(name="Install flatpak", packages=["flatpak"])

    # No dedicated pyinfra flatpak-remote operation, so check + shell out instead.
    existing_remotes = host.get_fact(Command, command="flatpak remote-list --columns=name") # pyright: ignore[reportUnknownMemberType]
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

    server.user(
        name="Allow access to webcams and USB ports",
        user=host.data.username,
        groups=["video", "dialout"],
        append=True,
    )

deploy_base()
