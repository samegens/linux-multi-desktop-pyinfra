# mint-desktop

pyinfra deploy that automates Sebastiaan's Linux Mint desktop setup and configuration. Rebuilt from
[`../fedora-desktop`](../fedora-desktop) (Ansible, Fedora KDE) using pyinfra instead of Ansible — same
spirit and conventions where they still apply, adapted for Mint/apt. This is a **lean core** rebuild,
not a full 1:1 port; see "Scope" in README.md for what's deliberately not ported yet.

## Secrets model (important)

This repo assumes a **sibling directory** `../desktop-secrets` containing `secrets_data.py`: a plain
Python module of `privy`-encrypted string constants (SSH private keys, tokens, etc). It is shared —
other repos can symlink and `import` the same file, not just this one.

- `pyinfra/secrets_data.py` is a **symlink** into `../desktop-secrets/secrets_data.py`, created by
  `setup-repo.sh`. Never assume its content is plaintext — every value is a `privy.hide()` token.
- `pyinfra/secrets.py` provides `reveal(hidden: str) -> bytes`, which decrypts using a password resolved
  in this order: `$VAULT_PASSWORD` env var → `~/Dropbox/ansible/.vault_pass` (the **same** password file
  `fedora-desktop`'s `vault-client.sh` already uses — don't create a second one).
  Fails loudly if neither is available.
- To add/rotate a secret: `privy.hide(data: bytes, password: str) -> str` in `../desktop-secrets`, paste
  the resulting token as a new constant in `secrets_data.py`. The token is ASCII-safe and can be embedded
  directly as a Python string literal.
- `.gitleaks.toml`/`.secrets.baseline` + the `secrets-detection.yml` CI workflow exist specifically to
  catch plaintext secrets leaking into this repo — don't bypass or weaken them.

## Two run modes: local vs remote

The same deploy (`pyinfra/deploy.py`) targets either:
- **`localhost`** (`@local` in `pyinfra/inventory.py`) — reconfigure the machine you're on. Run via
  `cd pyinfra && ./run-local.sh <extra pyinfra args>`.
- **`remote`** / **`raaf`** — bootstrap a different machine over SSH. Run via
  `cd pyinfra && ./run.sh <host> <extra pyinfra args>`.

Both go through `pyinfra/_run.sh`, which tees output to a timestamped log file under `/var/log/pyinfra`
and runs `pyinfra inventory.py deploy.py --sudo --diff`. pyinfra prints its own per-operation
Hosts/Success/Error/No-Change results table at the end of every run — there is no separate log-summarizer
tool here (fedora-desktop's `summarize_log.py` was dropped as unnecessary; pyinfra's own output already
does that job).

## Inventory hosts (`pyinfra/inventory.py`)

- `localhost` — the current machine (`@local` connector, no SSH).
- `raaf` — a specific physical box (mirrors the same host in `fedora-desktop`).
- `remote` — not a fixed machine; a generic placeholder host used when configuring *some* new/different
  desktop machine from the current one.

## Layout

- `pyinfra/deploy.py` — the main entrypoint; imports and calls each module's `deploy()`
  (`pyinfra/modules/*.py`), one file per feature/tool — equivalent to `fedora-desktop/ansible/tasks/*.yml`.
- `pyinfra/group_data/all.py` — shared vars (username, package lists, tool versions). Per-host overrides
  live in `pyinfra/group_data/<host>.py`.
- `pyinfra/files/` — static files pushed to machines (dotfiles, configs). `pyinfra/templates/` — Jinja2
  templates rendered via `files.template`.
- `pyinfra/modules/desktop/` — swappable per-desktop-environment module, dispatched on
  `group_data.desktop_environment`. Currently placeholders (Cinnamon/KDE/Xfce) — the target DE isn't
  finalized yet.
- `inspec/mint-desktop/` — Inspec/Cinc Auditor controls that verify the deploy actually configured the
  machine correctly. Run locally with `./test-local.sh` (uses `cinc-auditor`, matching `fedora-desktop`).
- `setup-repo.sh` — one-time repo bootstrap: symlinks `pyinfra/secrets_data.py` from `../desktop-secrets`.
- `prepare.sh` — bootstraps pyinfra itself on a fresh box (creates `~/python3-venv/pyinfra-latest`,
  installs `requirements.txt` into it) before the deploy can run.

## CI (`.github/workflows/ci.yml`)

Two jobs: `ruff check pyinfra/` (lint), and a `pyinfra inventory.py deploy.py --dry -y` smoke-check
against `@local` on the GitHub Ubuntu runner (catches import errors / broken operation calls even though
host facts differ from a real Mint box). A separate `secrets-detection.yml` workflow scans pushes for
leaked secrets (Gitleaks, TruffleHog, detect-secrets), matching `fedora-desktop`.

## Conventions

- One module file per feature under `pyinfra/modules/`, each exposing a single `@deploy`-decorated
  function, imported and called from `pyinfra/deploy.py` — mirrors `fedora-desktop`'s
  one-task-file-per-feature pattern via `import_tasks`.
- To run a subset (pyinfra has no `--tags` equivalent): point the CLI at specific module files directly,
  e.g. `pyinfra inventory.py modules/git.py`.
- **TDD**: when adding a new tool/feature, write the failing Inspec/Cinc Auditor control(s) in
  `inspec/mint-desktop/controls/` first, confirm they fail (`./test-local.sh`), then write the pyinfra
  operations to make them pass.
