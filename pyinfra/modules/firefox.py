"""Firefox non-free video codec support. Fedora-only: enables RPMFusion's non-free repo, swaps ffmpeg-free
for full ffmpeg (fixes Floatplane video scrubbing), and installs libavcodec-freeworld. Mint
ships proprietary codecs out of the box (its installer already prompts to install them), so
there's nothing equivalent to do on the apt side.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.facts.server import Command, LinuxDistribution
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import dnf, server

import pkgmgr
from pkgmgr import PackageManager

def _enable_rpmfusion_nonfree():
    major_version = host.get_fact(LinuxDistribution)["major"] # pyright: ignore[reportUnknownMemberType]
    dnf.rpm(
        name="Enable RPMFusion non-free repo",
        src=(
            "https://mirrors.rpmfusion.org/nonfree/fedora/"
            f"rpmfusion-nonfree-release-{major_version}.noarch.rpm"
        ),
    )

def _swap_ffmpeg_free_for_full():
    # `rpm -q` prints "package ... is not installed" to *stdout* (not stderr) when absent, so
    # checking that output for emptiness never works - it's non-empty either way. Check the
    # exit status via a marker string instead.
    installed = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command="rpm -q ffmpeg-free >/dev/null 2>&1 && echo present || true"
    )
    if not installed or installed.strip() != "present":
        host.noop("ffmpeg-free not installed - nothing to swap")
        return

    server.shell(
        name="Swap ffmpeg-free for full ffmpeg",
        commands=["dnf swap -y ffmpeg-free ffmpeg --allowerasing"],
    )

@deploy("Configure Firefox codec support")
def deploy_firefox():
    pm = pkgmgr.get_package_manager()
    match pm:
        case PackageManager.DNF:
            _enable_rpmfusion_nonfree()
            _swap_ffmpeg_free_for_full()
            pkgmgr.install(name="Install libavcodec-freeworld", packages=["libavcodec-freeworld"])
        case PackageManager.APT:
            host.noop("Mint ships proprietary codecs out of the box - nothing to do")
        case _:
            assert_never(pm)

deploy_firefox()
