"""Shared vars for every host."""

username = "sebastiaan"
git_user_name = "Sebastiaan"
git_user_email = "sebastiaan@blauwe-lucht.nl"

# Dispatches pyinfra/modules/desktop/__init__.py. Undecided - leave unset until a target
# desktop environment is picked.
desktop_environment = None

starship_version = "v1.23.0"
go_version = "1.26.3"

# Used to build cinc-auditor's .deb download URL (downloads.cinc.sh has no "latest" alias).
cinc_auditor_version = "7.1.7"
ubuntu_release = "22.04"

apt_packages = [
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
ssh_key_names = []
