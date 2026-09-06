"""TagUI (RPA automation) plus what it needs: Google Chrome to drive, PHP, and the
blauwe-lucht-rpa Google service-account key.

No apt/dnf archive ships TagUI - GitHub releases only, so this pins a version like every other
GitHub-releases-only module here.
"""

from io import BytesIO
from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.operations import apt, dnf, files

import pkgmgr
import secrets_data
import vault
from archives import download_and_extract
from pkgmgr import PackageManager

CHROME_DNF_REPO_FILE = "/etc/yum.repos.d/google-chrome.repo"
CHROME_APT_REPO_FILE = "/etc/apt/sources.list.d/google-chrome.list"
CHROME_APT_KEYRING_PATH = "/etc/apt/keyrings/google-chrome.gpg"

def _ensure_chrome_dnf_repo():
    if host.get_fact(File, path=CHROME_DNF_REPO_FILE): # pyright: ignore[reportUnknownMemberType]
        host.noop("Google Chrome dnf repo already configured")
        return

    dnf.repo(
        name="Add Google Chrome dnf repo",
        src="google-chrome",
        baseurl="https://dl.google.com/linux/chrome/rpm/stable/x86_64",
        description="google-chrome",
        gpgcheck=True,
        gpgkey="https://dl.google.com/linux/linux_signing_key.pub",
    )

def _ensure_chrome_apt_repo():
    if host.get_fact(File, path=CHROME_APT_REPO_FILE): # pyright: ignore[reportUnknownMemberType]
        host.noop("Google Chrome apt repo already configured")
        return

    apt.key(
        name="Add Google Chrome GPG key",
        src="https://dl.google.com/linux/linux_signing_key.pub",
        dest="google-chrome.gpg",
    )
    apt.repo(
        name="Add Google Chrome apt repo",
        src=(
            f"deb [arch=amd64 signed-by={CHROME_APT_KEYRING_PATH}] "
            "https://dl.google.com/linux/chrome/deb/ stable main"
        ),
        filename="google-chrome",
    )
    # Force a real refresh - base.py already ran apt.update(cache_time=3600) earlier in the
    # deploy, so the routine cached update wouldn't pick up this brand new source until the
    # cache_time window expires. Same fix as vscode.py/docker.py's _ensure_apt_repo().
    apt.update(name="Refresh apt cache for new Google Chrome repo")

def _install_chrome():
    username = host.data.username
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            _ensure_chrome_dnf_repo()
        case PackageManager.APT:
            _ensure_chrome_apt_repo()
        case _:
            assert_never(pm)

    pkgmgr.install(name="Install Google Chrome", packages=["google-chrome-stable"])

    for relative_dir in ["google-chrome", "google-chrome/Default"]:
        files.directory(
            name=f"Create ~/{relative_dir}",
            path=f"/home/{username}/{relative_dir}",
            user=username,
            group=username,
            mode="700",
            _sudo=False,
        )

def _install_tagui():
    username = host.data.username
    version = host.data.tagui_version
    url = f"https://github.com/kelaberetiv/TagUI/releases/download/v{version}/TagUI_Linux.zip"

    # Not files.download + files.unarchive - files.unarchive checks its source archive exists
    # via a fact at operation-definition time, which fails on a fresh (no -y) preview since the
    # preceding files.download has only been *queued*, not yet executed, at that point. Use the
    # custom archives.download_and_extract operation instead - see its docstring.
    download_and_extract(
        name=f"Download and extract TagUI {version}",
        url=url,
        dest=f"/home/{username}",
        # A specific file, not the bare "tagui" directory - archives.download_and_extract's
        # creates check uses the File fact, which only ever matches regular files and silently
        # stays None (never idempotent) for a directory path.
        creates=f"/home/{username}/tagui/src/tagui",
        user=username,
        group=username,
    )

    files.link(
        name="Link tagui executable",
        path="/usr/local/bin/tagui",
        target=f"/home/{username}/tagui/src/tagui",
    )

def _install_service_account_key():
    username = host.data.username
    files.put(
        name="Install blauwe-lucht-rpa Google service account key",
        src=BytesIO(vault.reveal(secrets_data.BLAUWE_LUCHT_RPA_SERVICE_ACCOUNT)),
        dest=f"/home/{username}/blauwe-lucht-rpa-f89be6fb53f3.json",
        user=username,
        group=username,
        mode="600",
        _sudo=False,
    )

@deploy("Install TagUI")
def deploy_tagui():
    _install_chrome()
    # unzip: needed by archives.download_and_extract below. php: required by TagUI itself.
    pkgmgr.install(name="Install TagUI prerequisites", packages=["unzip", "php"])
    _install_tagui()
    _install_service_account_key()

deploy_tagui()
