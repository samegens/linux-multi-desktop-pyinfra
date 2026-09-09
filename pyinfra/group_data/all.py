"""Shared vars for every host."""

username = "sebastiaan"
git_user_name = "Sebastiaan"
git_user_email = "sebastiaan@blauwe-lucht.nl"

# Set per-host in group_data/<host>.py to rename the machine. Left unset (None) here so base
# skips it rather than blanking the hostname on a host that didn't ask for one.
hostname: str | None = None

starship_version = "v1.23.0"
go_version = "1.26.3"

cinc_auditor_version = "7.1.7"

doublecmd_version = "1.2.7"

ghostty_apt_version = "1.3.1-0-ppa2"

balena_etcher_version = "2.1.6"

dotnet_version = "10.0.302"
powershell_version = "7.6.4"

tagui_version = "6.110.0"

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
    "moreutils",
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
    "com.prusa3d.PrusaSlicer",
]

hosts_entries = [
    "# Test/staging environments",
    "192.168.34.10  thuis-tst.blauwe-lucht.nl",
    "192.168.34.10  samtris-tst.blauwe-lucht.nl",
    "192.168.34.10  oogdesmeesters-tst.blauwe-lucht.nl",
    "192.168.34.10  fitlet-tst",
    "192.168.34.10  walangtext-tst.blauwe-lucht.nl",
    "192.168.34.10  miro-card-shuffle-dev-tst.blauwe-lucht.nl",
    "192.168.34.20  walangtext-tst.blauwelucht.nl",
    "192.168.34.20  samtris-tst.blauwelucht.nl",
    "192.168.34.20  oogdesmeesters-tst.blauwelucht.nl",
    "192.168.34.20  liteserver-tst",
    "",
    "# Remote hosts",
    "5.2.74.226     liteserver",
    "20.229.92.206  fitlet-acc",
    "",
    "# Local dev loopback aliases",
    "127.0.0.1 kuard.local",
    "127.0.0.1 rabbitmq.local",
    "127.0.0.1 dev.kuard.local",
    "127.0.0.1 demo.kuard.local",
    "127.0.0.1 kuard.dev.local",
    "127.0.0.1 kuard.prod.local",
    "127.0.0.1 game-collection.local",
    "127.0.0.1 samtris.local",
    "127.0.0.1 custom.local",
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
    "desktop",
]
