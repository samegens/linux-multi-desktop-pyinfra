# Linux Multi Desktop Configuration using pyinfra

[![CI](https://github.com/samegens/linux-multi-desktop-pyinfra/actions/workflows/ci.yml/badge.svg)](https://github.com/samegens/linux-multi-desktop-pyinfra/actions/workflows/ci.yml)
[![Secret Detection](https://github.com/samegens/linux-multi-desktop-pyinfra/actions/workflows/secrets-detection.yml/badge.svg)](https://github.com/samegens/linux-multi-desktop-pyinfra/actions/workflows/secrets-detection.yml)

pyinfra deploy that automates my Linux desktop setup and configuration, targeting Linux Mint, Fedora and Ubuntu from a single codebase.

## Features

- lean core deploy, one module per feature under `pyinfra/modules/`
- targets both apt and dnf — `pyinfra/pkgmgr.py` dispatches package
  installs/names/service names/config-file-path differences on `PackageManager`, keyed from a
  `Distro → PackageManager` mapping; adding a distro that shares an existing package manager
  is a one-line addition to that mapping
- desktop-environment module is swappable (`pyinfra/modules/desktop/`) — Cinnamon/KDE/Xfce placeholders,
  filled in once the target desktop environment is decided
- secrets (SSH keys, tokens) kept in a sibling `desktop-secrets` directory as `privy`-encrypted Python
  string constants, symlinked in by `setup-repo.sh`
- Inspec/Cinc Auditor controls (`inspec/mint-desktop`) verify the deploy actually configured the machine,
  runnable locally against `localhost` (`./test-local.sh`) or a remote host (`./test-remote.sh <group>`)
- `./check.sh` runs everything CI runs (pyright, unit tests, Inspec profile check) — meant to be run
  locally before pushing, not just in CI
- GitHub CI and secrets-detection pipelines
- [git commit hooks](.githooks) (enabled by `setup-repo.sh`) run the same gitleaks/TruffleHog/
  detect-secrets checks locally, before a secret ever leaves your machine

## Setup

1. Clone the repository
2. Run [`./prepare.sh`](prepare.sh) to bootstrap the `pyinfra-latest` virtualenv
3. Create the `desktop-secrets` directory next to this repo (see `pyinfra/vault.py` for the expected
   format) and run [`./setup-repo.sh`](setup-repo.sh) to symlink `pyinfra/secrets_data.py` into it
   and enable the [git commit hooks](.githooks)
4. Set your vault password: `$VAULT_PASSWORD` env var, or `~/Dropbox/ansible/.vault_pass`
5. Run the deploy:

   ```bash
   . ~/python3-venv/pyinfra-latest/bin/activate
   cd pyinfra && pyinfra inventory.py all.py --limit <group>
   ```

   where group is one of `localhost`, `mint_vm`, `dell_laptop`, or `raaf`.

## Scope

This is a rebuild from scratch using fedora-desktop as starting point/inspiration.
Ported so far: base packages,
git, SSH, bashrc/dotfiles, starship, Go, Rust, VS Code (editor, extensions, config files), Python
venvs (`~/python3-venv/*`, incl. this repo's own `pyinfra-latest`), Cinc Auditor, Docker (Engine +
Compose plugin, from Docker's own apt/dnf repo), k3s, Firefox non-free codecs (Fedora only), Double
Commander, Ghostty, Workrave, .NET SDK + PowerShell, Claude Code, JetBrainsMono Nerd Font,
Google Fonts, Microsoft core/ClearType fonts, inotify watch/instance sysctl limits, Fastfetch,
Dropbox, NFS/SSHFS mounts, Gitleaks, TruffleHog — all verified idempotent on both Mint (`mint_vm`
test VM) and Fedora (`localhost`).

Desktop-environment content is limited to panel-pinning so far (`pyinfra/panel_pin.py`, called
from `ghostty.py`, `vscode.py`, `doublecmd.py`, `obsidian.py`, `keepassxc.py`, `betterbird.py`),
dispatched on an autodetected `desktop_env.DesktopEnvironment` (KDE Plasma and Cinnamon only).

Still to come, same lean-core list, one module + Inspec control at a time: Node.js,
desktop-environment placeholder.

Not yet ported (add on demand, following the existing `pyinfra/modules/*.py` pattern):
printer, VeraCrypt, TagUI,
VirtualBox/Vagrant, NVIDIA, GRUB tweaks, hibernate, SELinux, Miniconda,
P4Merge, Terraform/Packer, personal `/etc/hosts` entries.

## Secret Detection

This repository uses multiple tools to prevent secret leaks:

- **Gitleaks**: Pattern-based detection
- **TruffleHog**: Entropy-based detection
- **detect-secrets**: Context-aware detection

The [pre-commit hook](.githooks/pre-commit) runs all three locally before a commit is even created;
the [secrets detection workflow](.github/workflows/secrets-detection.yml) runs the same checks again
on push as a backstop (also nightly, to catch newly-published detection rules independent of code
changes). In addition, secret *values* themselves are `privy`-encrypted before they ever reach
this repo (see [`pyinfra/vault.py`](pyinfra/vault.py)).
