"""JetBrainsMono Nerd Font - patched monospace font with Nerd Font glyphs (icons/symbols),
installed system-wide for all users. A single upstream release archive contains both the
ligature and NL (no-ligatures) variants, so one download covers "JetBrainsMono Nerd Font" and
"JetBrainsMonoNL Nerd Font" - confirmed live against the v3.5.0 JetBrainsMono.tar.xz release
asset, which lists both JetBrainsMonoNerdFont-Regular.ttf and JetBrainsMonoNLNerdFont-Regular.ttf
(plus every weight/style of each) in the same archive.

Always installs whatever nerd-fonts release is currently latest, not a pinned version like
starship_version/go_version elsewhere in this repo - deliberate per-module choice (user request),
same pattern as modules/k3s.py's Helm/k9s installs. The extract dir is version-suffixed
(jetbrains-mono-nerd-font-{version}) for the same reason Helm/k9s use a version-suffixed /opt
dir: it's how the idempotency check tells "already on latest" apart from "a new version shipped"
without needing to track installed state separately. Old-version dirs are left behind on a
version bump rather than cleaned up, same as Helm/k9s's /opt dirs - harmless, not worth the
extra complexity.

Also installs a couple of decorative Google Fonts. Playfair Display ships
upstream as a single variable-weight file (`PlayfairDisplay[wght].ttf`).
The `[wght]` brackets must stay percent-encoded
(`%5Bwght%5D`) in the download URL itself - unencoded, pyinfra's files.download shells out to
curl, which parses `[...]` as its own range-globbing syntax and fails with "bad range in URL" -
confirmed live against `localhost`.

Also installs the Microsoft core fonts (Arial, Times New Roman, etc.) and ClearType collection
(Calibri, Consolas, etc.) by fetching the same sourceforge mscorefonts2 mirror both Debian's
ttf-mscorefonts-installer and Fedora RPM Fusion's lpf-mscore-fonts/lpf-cleartype-fonts pull
from at install time - these fonts are "non-redistributable, no modifications permitted" so no
distro bundles the .ttf files themselves, only a fetch-on-install recipe. Rejected the packaged
options: `mscore-fonts-all` no longer exists on Fedora (confirmed via `dnf info` - RPM Fusion
replaced it with `lpf-mscore-fonts`, a bootstrap package that needs a separate `rpmbuild`/`mock`
build step, not a plain install); `ttf-mscorefonts-installer` on Mint would work but needs a
debconf EULA preseed and only covers the classic corefonts, not ClearType. Fetching the .exe/.EXE
cabs directly instead keeps Mint and Fedora on one identical code path. PowerPointViewer.exe (the
ClearType source) is an MSI installer, not a plain CAB like the others - cabextract's first pass
only unwraps it to an inner ppviewer.cab, which needs its own second cabextract pass to reach the
.ttf files - confirmed live.
"""

from io import StringIO
from urllib.parse import unquote

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.operations import files, server

import pkgmgr
from archives import download_and_extract
from github import latest_release_tag
from paths import PYINFRA_CACHE_DIR

GOOGLE_FONTS_DIR = "/usr/share/fonts/google-fonts"
GOOGLE_FONT_URLS = [
    "https://raw.githubusercontent.com/google/fonts/main/ofl/greatvibes/GreatVibes-Regular.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
]

def _font_filename(url: str) -> str:
    return unquote(url.rsplit("/", 1)[-1])

MSCOREFONTS_DIR = "/usr/share/fonts/mscorefonts"
MSCOREFONTS_INSTALL_SCRIPT = f"{PYINFRA_CACHE_DIR}/install-mscorefonts.sh"
MSCOREFONTS_URLS = [
    # Classic "core fonts of the web" - one .exe per family.
    "https://downloads.sourceforge.net/corefonts/the%20fonts/final/andale32.exe",
    "https://downloads.sourceforge.net/corefonts/the%20fonts/final/arialb32.exe",
    "https://downloads.sourceforge.net/corefonts/the%20fonts/final/comic32.exe",
    "https://downloads.sourceforge.net/corefonts/the%20fonts/final/courie32.exe",
    "https://downloads.sourceforge.net/corefonts/the%20fonts/final/georgi32.exe",
    "https://downloads.sourceforge.net/corefonts/the%20fonts/final/impact32.exe",
    "https://downloads.sourceforge.net/corefonts/the%20fonts/final/webdin32.exe",
    # European Union Expansion Update - newer Times New Roman/Trebuchet MS/Verdana.
    "https://sourceforge.net/projects/mscorefonts2/files/cabs/EUupdate.EXE",
    # ClearType collection (Calibri, Cambria, Candara, Consolas, Constantia, Corbel) -
    # bundled with the free PowerPoint Viewer installer, the same source lpf-cleartype-fonts
    # uses.
    "https://sourceforge.net/projects/mscorefonts2/files/cabs/PowerPointViewer.exe",
]

def _mscorefonts_install_script() -> str:
    urls = "\n".join(f'    "{url}"' for url in MSCOREFONTS_URLS)
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "\n"
        "work_dir=$(mktemp -d)\n"
        "trap 'rm -rf \"$work_dir\"' EXIT\n"
        "cd \"$work_dir\"\n"
        "\n"
        "urls=(\n"
        f"{urls}\n"
        ")\n"
        "for url in \"${urls[@]}\"; do\n"
        "    curl -fsSL -O \"$url\"\n"
        "done\n"
        "\n"
        "cabextract -q *\n"
        "shopt -s nullglob\n"
        "cab_files=(*.cab *.CAB)\n"
        "if [ ${#cab_files[@]} -gt 0 ]; then\n"
        '    cabextract -q "${cab_files[@]}"\n'
        "fi\n"
        "\n"
        f'mkdir -p "{MSCOREFONTS_DIR}"\n'
        f'find . -iname "*.ttf" -exec cp -t "{MSCOREFONTS_DIR}" {{}} +\n'
    )

@deploy("Install JetBrainsMono Nerd Font")
def deploy_jetbrains_mono_nerd_font():
    version = latest_release_tag("ryanoasis/nerd-fonts")
    font_dir = f"/usr/share/fonts/jetbrains-mono-nerd-font-{version}"

    extract_result = download_and_extract(
        name="Download and extract JetBrainsMono Nerd Font",
        url=f"https://github.com/ryanoasis/nerd-fonts/releases/download/{version}/JetBrainsMono.tar.xz",
        dest=font_dir,
        creates=f"{font_dir}/JetBrainsMonoNerdFont-Regular.ttf",
    )

    server.shell(
        name="Rebuild JetBrainsMono Nerd Font cache",
        commands=[f"fc-cache -f {font_dir}"],
        _if=extract_result.did_change,
    )

@deploy("Install Google Fonts")
def deploy_google_fonts():
    files.directory(
        name="Create Google Fonts directory",
        path=GOOGLE_FONTS_DIR,
    )

    missing_urls = [
        url for url in GOOGLE_FONT_URLS
        if not host.get_fact(File, path=f"{GOOGLE_FONTS_DIR}/{_font_filename(url)}") # pyright: ignore[reportUnknownMemberType]
    ]

    for url in missing_urls:
        files.download(
            name=f"Download {_font_filename(url)}",
            src=url,
            dest=f"{GOOGLE_FONTS_DIR}/{_font_filename(url)}",
        )

    if missing_urls:
        server.shell(
            name="Rebuild Google Fonts font cache",
            commands=[f"fc-cache -f {GOOGLE_FONTS_DIR}"],
        )

@deploy("Install Microsoft core/ClearType fonts")
def deploy_mscorefonts():
    sentinel = f"{MSCOREFONTS_DIR}/Arial.ttf"
    if host.get_fact(File, path=sentinel): # pyright: ignore[reportUnknownMemberType]
        host.noop("Microsoft core/ClearType fonts already installed")
        return

    pkgmgr.install(name="Install cabextract", packages=["cabextract"])

    files.put(
        name="Upload Microsoft fonts install script",
        src=StringIO(_mscorefonts_install_script()),
        dest=MSCOREFONTS_INSTALL_SCRIPT,
        mode="755",
    )
    server.shell(
        name="Download and extract Microsoft core/ClearType fonts",
        commands=[MSCOREFONTS_INSTALL_SCRIPT],
    )
    server.shell(
        name="Rebuild Microsoft fonts font cache",
        commands=[f"fc-cache -f {MSCOREFONTS_DIR}"],
    )

deploy_jetbrains_mono_nerd_font()
deploy_google_fonts()
deploy_mscorefonts()
