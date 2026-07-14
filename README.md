# Mint Desktop Configuration

pyinfra deploy that automates Sebastiaan's Linux Mint desktop setup and configuration.
Sibling of [`fedora-desktop`](../fedora-desktop) (Ansible/Fedora KDE) — same spirit, rebuilt with
pyinfra instead of Ansible, and Mint/apt instead of Fedora/dnf.

## Features

- lean core deploy: base packages, dotfiles, git, SSH, dev toolchain (Go/Rust/Node), Docker, VS Code
- desktop-environment module is swappable (`pyinfra/modules/desktop/`) — Cinnamon/KDE/Xfce placeholders,
  filled in once the target desktop environment is decided
- secrets (SSH keys, tokens) kept in a sibling `desktop-secrets` directory as `privy`-encrypted Python
  string constants, symlinked in by `setup-repo.sh` — shareable with other repos (not just this one)
- wrapper scripts (`pyinfra/run.sh` / `run-local.sh`) log every run to a timestamped file
- Inspec/Cinc Auditor controls (`inspec/mint-desktop`) verify the deploy actually configured the machine
- GitHub Actions CI (lint + dry-run smoke test) and a separate secrets-detection workflow (Gitleaks,
  TruffleHog, detect-secrets)

## Setup

1. Clone the repository
2. Run [`./prepare.sh`](prepare.sh) to bootstrap the `pyinfra-latest` virtualenv
3. Create the `desktop-secrets` directory next to this repo (see `pyinfra/secrets.py` for the expected
   format) and run [`./setup-repo.sh`](setup-repo.sh) to symlink `pyinfra/secrets_data.py` into it
4. Set your vault password: `$VAULT_PASSWORD` env var, or `~/Dropbox/ansible/.vault_pass` (shared with
   `fedora-desktop`)
5. Run the deploy:
   - Local: `cd pyinfra && ./run-local.sh`
   - Remote: `cd pyinfra && ./run.sh <host>`

## Scope

This is a **lean core** rebuild, not a full 1:1 port of `fedora-desktop`. Ported so far: base packages,
git, SSH, bashrc/dotfiles, starship, Go, Rust, Node.js, Docker, VS Code, Python venv bootstrap,
Cinc Auditor.

Deliberately not yet ported (add on demand, following the existing `pyinfra/modules/*.py` pattern):
printer, VeraCrypt, TagUI, balenaEtcher, Double Commander, Darktable, Obsidian, Workrave,
VirtualBox/Vagrant, k3s, NVIDIA, GRUB tweaks, hibernate, SELinux, Google Fonts, Miniconda,
gitleaks/trufflehog *install* tasks, P4Merge, Terraform/Packer, NFS/SSHFS mounts, Fastfetch,
MS TTF fonts, personal `/etc/hosts` entries.

## Secret Detection

This repository uses multiple tools to prevent secret leaks:

- **Gitleaks**: Pattern-based detection
- **TruffleHog**: Entropy-based detection
- **detect-secrets**: Context-aware detection

The [secrets detection workflow](.github/workflows/secrets-detection.yml) automatically scans for
secrets on push. In addition, secret *values* themselves are `privy`-encrypted before they ever reach
this repo (see [`pyinfra/secrets.py`](pyinfra/secrets.py)).
