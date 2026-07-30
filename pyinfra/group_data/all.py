"""Shared vars for every host."""

from pkgmgr import Distro

username = "sebastiaan"
git_user_name = "Sebastiaan"
git_user_email = "sebastiaan@blauwe-lucht.nl"

# Dispatches pyinfra/modules/desktop/__init__.py. Undecided - leave unset until a target
# desktop environment is picked.
desktop_environment = None

# Only pkgmgr.py switches on this directly - everything else (package installs, service
# names, config paths) switches on PackageManager instead, via pkgmgr.get_package_manager().
# Leave unset (None) on any host until its distro is deliberately decided - get_distro()
# fails loudly instead of guessing.
distro: Distro | None = None

starship_version = "v1.23.0"
go_version = "1.26.3"

cinc_auditor_version = "7.1.7"

doublecmd_version = "1.2.7"

vscode_extensions = [
    "redhat.ansible",
    "redhat.vscode-yaml",
    "yzhang.markdown-all-in-one",
    "mhutchie.git-graph",
    "ms-dotnettools.csdevkit",
    "ms-vscode-remote.remote-ssh",
    "ms-vscode-remote.remote-containers",
    "ms-vscode.cpptools-extension-pack",
    "ms-vscode.cmake-tools",
    "ms-python.python",
    "blauwelucht.ansible-go-to-definition",
    "rust-lang.rust-analyzer",
    "eamodio.gitlens",
    "esbenp.prettier-vscode",
    "hediet.vscode-drawio",
    "edgardmessias.clipboard-manager",
    "dbaeumer.vscode-eslint",
    "davidanson.vscode-markdownlint",
    "bierner.markdown-mermaid",
    "docker.docker",
    "tomoki1207.pdf",
    "platformio.platformio-ide",
    "github.vscode-github-actions",
]

packages = [
    "byobu",
    "vim",
    "keepassxc",
    "okular",
    "smbclient",
    "imagemagick",
    "htop",
    "jq",
    "gimp",
    "gh",
    "ncdu",
    "vlc",
    "inkscape",
    "traceroute",
    "simple-scan",
    "sshpass",
]

flatpaks = [
    "md.obsidian.Obsidian",
    "com.slack.Slack",
    "com.spotify.Client",
    "org.signal.Signal",
    "com.jgraph.drawio.desktop",
    "ch.protonmail.protonmail-bridge",
    "eu.betterbird.Betterbird",
]

# See pyinfra/modules/ssh.py for how to add an entry.
ssh_key_names = [
    "cubi",
    "fitpc",
    "fitlet",
    "fitlet-tst",
    "fitlet-acc",
    "liteserver",
    "liteserver-tst",
    "github_samegens",
    "github_blauwe-lucht",
    "gitlab",
    "github_adopteerregenwoud",
    "bhosted",
]
