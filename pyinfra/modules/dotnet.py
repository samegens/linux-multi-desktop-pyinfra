""".NET SDK + PowerShell, both installed from Microsoft's own upstream release artifacts rather
than distro packages - deliberately sidesteps the whole class of problem documented in
vscode.py's docstring: fedora-desktop's old Ansible task installed dotnet-sdk-8.0 as a native
Fedora dnf package via the Microsoft prod repo, which collided with Fedora's own package
namespace and needed a global excludepkgs hack (for azure-cli) that ended up breaking installs
outright under dnf5. There's no apt equivalent of that repo/package at all, so a pkgmgr.py-style
per-package-manager name override could never have covered Mint anyway.

Both dotnet-install.sh (Microsoft's own documented install mechanism, built specifically to work
identically on any glibc Linux distro without touching apt/dnf) and PowerShell's "portable"
linux-x64 tar.gz release asset are self-contained - no PackageManager dispatch needed here at
all, same shape as k3s.py/doublecmd.py/starship.py. Installed into version-suffixed /opt dirs and
symlinked onto PATH, matching doublecmd.py/starship.py's pattern.

/usr/local/bin/dotnet symlink alone is enough for the `dotnet` CLI itself (its muxer resolves the
install root via argv0's realpath) but NOT for a project *built* into a standalone apphost
executable and run directly (e.g. `./bin/Release/net.../MyApp`, as opposed to `dotnet run` or
`dotnet MyApp.dll`) - confirmed live: running a built apphost against only the PATH symlink fails
with "You must install .NET to run this application", since hostfxr's own resolution for that case
never consults PATH at all, only DOTNET_ROOT[_ARCH], /etc/dotnet/install_location[_ARCH], or the
hardcoded default /usr/share/dotnet. Also symlinking /usr/share/dotnet -> the install dir covers
that case for free, with no env var needed anywhere - simpler than setting DOTNET_ROOT in the
system bashrc (what the old Ansible task did for its differently-shaped dnf-package install).

DOTNET_ROOT via the system bashrc was considered and rejected as the *general* fix (not just for
the legacy-package case below): /etc/bash.bashrc/etc/bashrc only run for interactive shells, so
an SSH/Inspec/cron-run `dotnet`-built apphost - a non-interactive shell - would never see it. The
/usr/share/dotnet symlink works unconditionally regardless of shell type.

On `localhost` specifically, fedora-desktop's old Ansible task already installed .NET as native
Fedora dnf packages, which - confirmed live via `rpm -qf /usr/share/dotnet` - actually own that
directory (dotnet-hostfxr-8.0/dotnet-runtime-deps-8.0 own the dir itself, dotnet-sdk-8.0 owns
/usr/share/dotnet/sdk and friends). That has to be removed first so the symlink above has a clear
path to claim - see _remove_legacy_dnf_dotnet(). Confirmed via a `dnf remove --assumeno` dry run
that this cascades cleanly to aspnetcore-runtime-8.0 and now-unused weak deps
(aspnetcore-targeting-pack-8.0, netstandard-targeting-pack-2.1) with nothing outside the .NET
ecosystem pulled in - a real uninstall-then-install sequence, not two mechanisms fighting over the
same path at once. Mint has no such legacy state, so this is a dnf-only cleanup step. The
/usr/share/dotnet files.link uses force=True so a leftover non-symlink there (from a run where
the dnf removal above hasn't executed yet, or on a first pass before this module existed) gets
replaced rather than crashing the whole plan at prepare time - files.link's own fact-check raises
immediately otherwise, before any operation's commands actually execute (same prepare-vs-execute
ordering caveat as _fix_docker_deprecation_regex in cinc_auditor.py).

The pinned dotnet_version SDK only bundles its own major runtime (10.x). A csproj targeting an
older TargetFramework (e.g. net7.0) still *builds* fine - MSBuild doesn't reject down-level TFMs -
but *running* it needs that TargetFramework's actual shared runtime present, which an EOL SDK
doesn't ship. dotnet-install.sh's --runtime flag can install just the runtime (no SDK) for any
channel side-by-side into the same --install-dir, since runtimes live independently under
shared/Microsoft.NETCore.App/<version>/ - no conflict with the SDK already there. See
DOTNET_EXTRA_RUNTIME_CHANNELS/_install_extra_dotnet_runtimes().
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.facts.server import Command
from pyinfra.operations import dnf, files, server

from archives import download_and_extract

import pkgmgr
from pkgmgr import PackageManager
from paths import PYINFRA_CACHE_DIR

# fedora-desktop's old Ansible task installed these as native dnf packages - see module
# docstring. Just the packages dnf reported directly under "Removing:" in a dry run; dnf's own
# solver cascades to dependent/now-unused packages (aspnetcore-runtime-8.0 and friends) itself,
# same as a plain `dnf remove` would.
LEGACY_DNF_DOTNET_PACKAGES = [
    "dotnet-sdk-8.0",
    "dotnet-runtime-8.0",
    "dotnet-hostfxr-8.0",
    "dotnet-runtime-deps-8.0",
    "dotnet-apphost-pack-8.0",
    "dotnet-targeting-pack-8.0",
    "dotnet-host",
]

def _remove_legacy_dnf_dotnet():
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            dnf.packages(
                name="Remove legacy dnf-packaged .NET SDK",
                packages=LEGACY_DNF_DOTNET_PACKAGES,
                present=False,
            )
        case PackageManager.APT:
            pass
        case _:
            assert_never(pm)

# Channels whose runtime (not the full SDK) is installed side-by-side with the pinned SDK
# version, so csproj files targeting older/EOL TargetFrameworks can still run - see module
# docstring. Starts at net7.0 (oldest TFM this repo's projects still target); 10.0 is included
# for completeness even though the pinned SDK already bundles it - _install_extra_dotnet_runtimes
# skips it as a no-op once it finds the SDK's own runtime already there.
DOTNET_EXTRA_RUNTIME_CHANNELS = ["7.0", "8.0", "9.0", "10.0"]

DOTNET_INSTALL_SCRIPT = f"{PYINFRA_CACHE_DIR}/dotnet-install.sh"

def _ensure_dotnet_install_script():
    files.download(
        name="Download dotnet-install.sh",
        src="https://dot.net/v1/dotnet-install.sh",
        dest=DOTNET_INSTALL_SCRIPT,
        mode="755",
    )

def _install_dotnet_sdk(version: str) -> str:
    install_dir = f"/opt/dotnet-{version}"
    binary = f"{install_dir}/dotnet"

    if host.get_fact(File, path=binary): # pyright: ignore[reportUnknownMemberType]
        host.noop(f".NET SDK {version} is already installed")
    else:
        _ensure_dotnet_install_script()
        server.shell(
            name=f"Install .NET SDK {version}",
            commands=[f"{DOTNET_INSTALL_SCRIPT} --version {version} --install-dir {install_dir}"],
        )

    files.link(
        name="Link dotnet binary into /usr/local/bin",
        path="/usr/local/bin/dotnet",
        target=binary,
    )
    files.link(
        name="Link /usr/share/dotnet to the install dir",
        path="/usr/share/dotnet",
        target=install_dir,
        force=True,
    )
    return install_dir

def _install_extra_dotnet_runtimes(install_dir: str, channels: list[str]):
    for channel in channels:
        existing = host.get_fact( # pyright: ignore[reportUnknownMemberType]
            Command,
            command=f"ls -d {install_dir}/shared/Microsoft.NETCore.App/{channel}.* 2>/dev/null || true",
        )
        if existing:
            host.noop(f".NET {channel} runtime is already installed")
            continue

        _ensure_dotnet_install_script()
        server.shell(
            name=f"Install .NET {channel} runtime",
            commands=[
                f"{DOTNET_INSTALL_SCRIPT} --channel {channel} --runtime dotnet "
                f"--install-dir {install_dir}"
            ],
        )

def _install_powershell(version: str):
    extract_dir = f"/opt/powershell-{version}"
    binary = f"{extract_dir}/pwsh"

    download_and_extract(
        name="Download and extract PowerShell",
        url=(
            "https://github.com/PowerShell/PowerShell/releases/download/"
            f"v{version}/powershell-{version}-linux-x64.tar.gz"
        ),
        dest=extract_dir,
        creates=binary,
    )
    files.link(
        name="Link pwsh binary into /usr/local/bin",
        path="/usr/local/bin/pwsh",
        target=binary,
    )

@deploy("Install .NET SDK")
def deploy_dotnet():
    _remove_legacy_dnf_dotnet()
    install_dir = _install_dotnet_sdk(host.data.dotnet_version)
    _install_extra_dotnet_runtimes(install_dir, DOTNET_EXTRA_RUNTIME_CHANNELS)

@deploy("Install PowerShell")
def deploy_powershell():
    _install_powershell(host.data.powershell_version)

deploy_dotnet()
deploy_powershell()
