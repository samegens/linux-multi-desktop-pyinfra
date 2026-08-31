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
"""

from urllib.parse import unquote

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.files import File
from pyinfra.operations import files, server

from archives import download_and_extract
from github import latest_release_tag

GOOGLE_FONTS_DIR = "/usr/share/fonts/google-fonts"
GOOGLE_FONT_URLS = [
    "https://raw.githubusercontent.com/google/fonts/main/ofl/greatvibes/GreatVibes-Regular.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
]

def _font_filename(url: str) -> str:
    return unquote(url.rsplit("/", 1)[-1])

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

deploy_jetbrains_mono_nerd_font()
deploy_google_fonts()
