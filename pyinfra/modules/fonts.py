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
"""

from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import server

from archives import download_and_extract
from github import latest_release_tag

@deploy("Install JetBrainsMono Nerd Font")
def deploy_fonts():
    version = latest_release_tag("ryanoasis/nerd-fonts")
    font_dir = f"/usr/share/fonts/jetbrains-mono-nerd-font-{version}"

    extract_result = download_and_extract(
        name="Download and extract JetBrainsMono Nerd Font",
        url=f"https://github.com/ryanoasis/nerd-fonts/releases/download/{version}/JetBrainsMono.tar.xz",
        dest=font_dir,
        creates=f"{font_dir}/JetBrainsMonoNerdFont-Regular.ttf",
    )

    server.shell(
        name="Rebuild font cache",
        commands=[f"fc-cache -f {font_dir}"],
        _if=extract_result.did_change,
    )

deploy_fonts()
