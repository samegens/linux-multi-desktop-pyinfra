"""Visual Studio Code, installed from Microsoft's own apt/dnf repo (same "code" package name
under both), plus extensions and personal config files. Repo/key setup is genuinely
package-manager-specific (not a generic install-name override), so this module - unlike most
others - branches on PackageManager directly rather than adding a one-off case to pkgmgr.py."""

from typing import assert_never

from pyinfra.facts.files import File
from pyinfra.facts.server import Command
from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import apt, dnf, files, server

import pkgmgr
from pkgmgr import PackageManager
from panel_pin import pin_to_panel

import dbus_session

VSCODE_DESKTOP_FILE_ID = "code.desktop"

DNF_GPG_KEY_URL = "https://packages.microsoft.com/yumrepos/vscode/repodata/repomd.xml.key"
DNF_GPG_KEY_PATH = "/etc/pki/rpm-gpg/microsoft-vscode.asc"
APT_GPG_KEY_URL = "https://packages.microsoft.com/keys/microsoft.asc"
APT_KEYRING_PATH = "/etc/apt/keyrings/packages.microsoft.gpg"

def _ensure_dnf_repo():
    repo_file = "/etc/yum.repos.d/vscode.repo"
    if host.get_fact(File, path=repo_file): # pyright: ignore[reportUnknownMemberType]
        host.noop("VS Code dnf repo already configured")
        return

    files.download(name="Download Microsoft GPG key", src=DNF_GPG_KEY_URL, dest=DNF_GPG_KEY_PATH)
    dnf.repo(
        name="Add VS Code dnf repo",
        src="vscode",
        baseurl="https://packages.microsoft.com/yumrepos/vscode",
        description="Visual Studio Code",
        gpgcheck=True,
        gpgkey=f"file://{DNF_GPG_KEY_PATH}",
    )

def _ensure_apt_repo():
    repo_file = "/etc/apt/sources.list.d/vscode.list"
    if host.get_fact(File, path=repo_file): # pyright: ignore[reportUnknownMemberType]
        host.noop("VS Code apt repo already configured")
        return

    apt.key(name="Add Microsoft GPG key", src=APT_GPG_KEY_URL, dest="packages.microsoft.gpg")
    apt.repo(
        name="Add VS Code apt repo",
        src=f"deb [arch=amd64,arm64,armhf signed-by={APT_KEYRING_PATH}] "
        "https://packages.microsoft.com/repos/code stable main",
        filename="vscode",
    )
    # Force a real refresh - base.py already ran apt.update(cache_time=3600) earlier in the
    # deploy, so the routine cached update wouldn't pick up this brand new source until the
    # cache_time window expires.
    apt.update(name="Refresh apt cache for new VS Code repo")

def _install_extensions():
    username = host.data.username
    installed = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command="code --list-extensions 2>/dev/null || true",
        _sudo_user=username,
    )
    installed_names = (installed or "").splitlines()
    missing = [ext for ext in host.data.vscode_extensions if ext not in installed_names]

    if not missing:
        host.noop("VS Code extensions already installed")
        return

    server.shell(
        name="Install VS Code extensions",
        commands=[f"code --install-extension {ext} || true" for ext in missing],
        _sudo_user=username,
    )

def _copy_config_files():
    username = host.data.username
    config_dir = f"/home/{username}/.config/Code/User"

    for relative_dir in ["Code", "Code/User", "Code/User/snippets"]:
        files.directory(
            name=f"Create ~/.config/{relative_dir}",
            path=f"/home/{username}/.config/{relative_dir}",
            user=username,
            group=username,
            mode="755",
            _sudo=False,
        )

    for relative_path in ["keybindings.json", "settings.json", "snippets/csharp.json"]:
        files.put(
            name=f"Copy VS Code {relative_path}",
            src=f"files/vscode/{relative_path}",
            dest=f"{config_dir}/{relative_path}",
            user=username,
            group=username,
            mode="644",
            _sudo=False,
        )

def _disable_ibus_emoji_hotkey():
    """Ctrl-. is used by VS Code but IBus steals it for its emoji picker by default. Guarded
    to skip cleanly (not error) when there's no desktop/dbus session for gsettings to talk to -
    e.g. a headless verification VM."""
    username = host.data.username
    uid = dbus_session.resolve_uid(username)
    if not uid:
        host.noop("could not resolve uid - skipping IBus tweak")
        return

    env = dbus_session.get_dbus_env(uid)
    current = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=f"{env} gsettings get org.freedesktop.ibus.panel.emoji hotkey 2>/dev/null || true",
        _sudo_user=username,
    )
    if not current:
        host.noop("gsettings/ibus emoji schema unavailable - skipping (no desktop session?)")
        return

    if current.strip() == "['']":
        host.noop("IBus emoji hotkey already disabled")
        return

    server.shell(
        name="Disable Ctrl-. binding for emoji in IBus",
        commands=[f"{env} gsettings set org.freedesktop.ibus.panel.emoji hotkey \"['']\""],
        _sudo_user=username,
    )

@deploy("Install VS Code")
def deploy_vscode():
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            _ensure_dnf_repo()
        case PackageManager.APT:
            _ensure_apt_repo()
        case _:
            assert_never(pm)

    pkgmgr.install(name="Install VS Code", packages=["code"])
    _install_extensions()
    _copy_config_files()
    _disable_ibus_emoji_hotkey()

@deploy("Pin VS Code to panel")
def pin_vscode_to_panel():
    pin_to_panel(VSCODE_DESKTOP_FILE_ID, host.data.username)

deploy_vscode()
pin_vscode_to_panel()
