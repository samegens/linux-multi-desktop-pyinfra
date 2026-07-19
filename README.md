# Mint Desktop Configuration

[![CI](https://github.com/samegens/linux-mint-desktop/actions/workflows/ci.yml/badge.svg)](https://github.com/samegens/linux-mint-desktop/actions/workflows/ci.yml)
[![Secret Detection](https://github.com/samegens/linux-mint-desktop/actions/workflows/secrets-detection.yml/badge.svg)](https://github.com/samegens/linux-mint-desktop/actions/workflows/secrets-detection.yml)

pyinfra deploy that automates Sebastiaan's Linux desktop setup and configuration, targeting both
Linux Mint (apt) and Fedora (dnf) from a single codebase. Sibling of
[`fedora-desktop`](../fedora-desktop) (Ansible/Fedora KDE) — same spirit, rebuilt with pyinfra
instead of Ansible.

## Features

- lean core deploy, one module per feature under `pyinfra/modules/`
- targets both Mint/apt and Fedora/dnf — `pyinfra/pkgmgr.py` dispatches package
  installs/names/service names/config-file-path differences on `PackageManager`, keyed from a
  `Distro → PackageManager` mapping; adding a distro that shares an existing package manager
  (e.g. Ubuntu, already added) is a one-line addition to that mapping
- desktop-environment module is swappable (`pyinfra/modules/desktop/`) — Cinnamon/KDE/Xfce placeholders,
  filled in once the target desktop environment is decided
- secrets (SSH keys, tokens) kept in a sibling `desktop-secrets` directory as `privy`-encrypted Python
  string constants, symlinked in by `setup-repo.sh` — shareable with other repos (not just this one)
- wrapper scripts (`pyinfra/run.sh` / `run-local.sh`, log every run to a timestamped file) are planned
  but not yet built — see CLAUDE.md's "Current status"
- Inspec/Cinc Auditor controls (`inspec/mint-desktop`) verify the deploy actually configured the machine,
  runnable locally against `localhost` (`./test-local.sh`) or a remote host (`./test-remote.sh <group>`)
- `./check.sh` runs everything CI runs (pyright, unit tests, Inspec profile check) — meant to be run
  locally before pushing, not just in CI
- GitHub Actions CI (`check.sh`) and a separate secrets-detection workflow (Gitleaks, TruffleHog,
  detect-secrets)

## Setup

1. Clone the repository
2. Run [`./prepare.sh`](prepare.sh) to bootstrap the `pyinfra-latest` virtualenv
3. Create the `desktop-secrets` directory next to this repo (see `pyinfra/vault.py` for the expected
   format) and run [`./setup-repo.sh`](setup-repo.sh) to symlink `pyinfra/secrets_data.py` into it
4. Set your vault password: `$VAULT_PASSWORD` env var, or `~/Dropbox/ansible/.vault_pass` (shared with
   `fedora-desktop`)
5. Run the deploy (wrapper scripts not built yet, invoke pyinfra directly for now):

   ```bash
   cd pyinfra && ~/python3-venv/pyinfra-latest/bin/pyinfra inventory.py deploy.py --limit <group> -y
   ```

## Scope

This is a **lean core** rebuild, not a full 1:1 port of `fedora-desktop`. Ported so far: base packages,
git, SSH, bashrc/dotfiles, starship, Go — all verified idempotent on both Mint (`remote` test VM) and
Fedora (`localhost`).

Desktop-environment content (Cinnamon/KDE/Xfce) is not yet built — `pyinfra/modules/desktop/` is
still a placeholder, dispatched on `group_data.desktop_environment` once a target is decided.

Still to come, same lean-core list, one module + Inspec control at a time: Rust, Node.js, Docker,
VS Code, Python venv bootstrap, Cinc Auditor, desktop-environment placeholder.

Deliberately not yet ported (add on demand, following the existing `pyinfra/modules/*.py` pattern):
printer, VeraCrypt, TagUI, balenaEtcher, Double Commander, Darktable, Obsidian, Workrave,
VirtualBox/Vagrant, k3s, NVIDIA, GRUB tweaks, hibernate, SELinux, Google Fonts, Miniconda,
gitleaks/trufflehog *install* tasks, P4Merge, Terraform/Packer, NFS/SSHFS mounts, Fastfetch,
MS TTF fonts, personal `/etc/hosts` entries, SSH host aliases (`~/.ssh/config`).

## Secret Detection

This repository uses multiple tools to prevent secret leaks:

- **Gitleaks**: Pattern-based detection
- **TruffleHog**: Entropy-based detection
- **detect-secrets**: Context-aware detection

The [secrets detection workflow](.github/workflows/secrets-detection.yml) automatically scans for
secrets on push. In addition, secret *values* themselves are `privy`-encrypted before they ever reach
this repo (see [`pyinfra/vault.py`](pyinfra/vault.py)).
