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
- `pyinfra/vault.py` provides `reveal(hidden: str) -> bytes`, which decrypts using a password resolved
  in this order: `$VAULT_PASSWORD` env var → `~/Dropbox/ansible/.vault_pass` (the **same** password file
  `fedora-desktop`'s `vault-client.sh` already uses — don't create a second one).
  Fails loudly if neither is available. Not named `secrets.py`: that would shadow Python's stdlib
  `secrets` module for anything importing from `pyinfra/`.
- Inventory data (`pyinfra/inventory.py`) can also pull secrets directly, e.g. `ssh_password` for the
  `remote`/`raaf` hosts — see the `_remote_password = vault.reveal(...)` pattern there. `_sudo_password`
  must be set via host data using that exact underscore-prefixed key name (matching pyinfra's global
  argument name) for per-host sudo password override to actually take effect.
- To add/rotate a secret: `privy.hide(data: bytes, password: str) -> str` in `../desktop-secrets`, paste
  the resulting token as a new constant in `secrets_data.py`. The token is ASCII-safe and can be embedded
  directly as a Python string literal.
- `.gitleaks.toml`/`.secrets.baseline` + the `secrets-detection.yml` CI workflow exist specifically to
  catch plaintext secrets leaking into this repo — don't bypass or weaken them.

## Two run modes: local vs remote

The same deploy (`pyinfra/deploy.py`) targets either:

- **`localhost`** (`@local` in `pyinfra/inventory.py`) — reconfigure the machine you're on.
- **`remote`** / **`raaf`** — bootstrap a different machine over SSH.

**Current way to invoke pyinfra** (from the `pyinfra/` dir, using the dedicated venv):

```bash
/home/sebastiaan/python3-venv/pyinfra-latest/bin/pyinfra inventory.py deploy.py --limit <group> -y
```

`run.sh` / `run-local.sh` / `_run.sh` wrapper scripts (mirroring `fedora-desktop`'s: tee output to a
timestamped log under `/var/log/pyinfra`, wrap the command above) are **planned but not yet built** — see
task 5 in the task list / this file's "Current status" section below. Don't assume they exist. pyinfra
prints its own per-operation Hosts/Success/Error/No-Change results table at the end of every run — there
is no separate log-summarizer tool here (fedora-desktop's `summarize_log.py` was dropped as unnecessary;
pyinfra's own output already does that job), so the wrapper scripts, once built, only need to add logging.

## Test VM (primary verification target this session)

This dev machine is Fedora, so `localhost`/`@local` runs here would deploy the wrong OS entirely - real
verification happens against a disposable **Linux Mint test VM**, currently reachable at
`192.168.149.134` (IP may change if the VM is recreated - check with the user if unreachable).

- Credentials: `secrets_data.SSH_PASSWORD`, used for **both** SSH login and sudo escalation (see the
  `_sudo_password` gotcha below). Decrypt via `vault.reveal(secrets_data.SSH_PASSWORD).decode()`.
- `pyinfra/inventory.py`'s `remote` group is currently pointed at this VM (`ssh_hostname`,
  `ssh_password`, `_sudo_password` all wired up already) - this is a temporary/pragmatic wiring for
  verification, not a real "remote" host in the fedora-desktop sense. Don't be surprised the placeholder
  host has a concrete IP.
- **Per-module dev loop** (do this one module at a time, don't batch):
  1. Write `pyinfra/modules/x.py` (self-invoking `deploy_x()` at the bottom, see gotchas below).
  2. `cd pyinfra && /home/sebastiaan/python3-venv/pyinfra-latest/bin/pyinfra inventory.py modules/x.py --limit remote -y`
     - run it for real (not `--dry` - see the `files.download`+`files.unarchive` dry-mode limitation
       below), inspect the results table.
  3. Run the exact same command again. Every operation must show "No Change" - if anything still shows
     "Success" on the second run, it's a real idempotency bug, not cosmetic (see gotchas below for the
     classes of bugs this has caught: wrong package names, symlink-vs-file, regex escaping, missing
     `creates=`, etc). Fix and repeat until clean.
  4. Add matching Inspec controls to `inspec/mint-desktop/controls/*.rb` (uncomment the relevant `# TODO:
     uncomment once modules/x.py is built` block if one already exists, or add new controls).
  5. `./test-remote.sh remote` - confirm the new controls pass too.
  6. Add `import modules.x  # pyright: ignore` to `pyinfra/deploy.py`.
  7. Update README.md's "Scope" section (ported vs. still-to-come) to reflect the new module.

## Current status

See README.md's **Scope** section for the up-to-date list of what's ported vs. deferred - keep it in sync
as modules land, it's the source of truth for progress, not this file. As of writing: `base`, `git`,
`ssh`, `bashrc`, `starship`, `go` are done and verified (idempotent + Inspec-covered) against the test VM.
Wrapper scripts (task 5), remaining lean-core modules (`rust`, `nodejs`, `docker`, `vscode`,
`python_venv`, `cinc_auditor`, `desktop` placeholder), and final end-to-end verification are outstanding.

## Inventory hosts (`pyinfra/inventory.py`)

- `localhost` — the current machine (`@local` connector, no SSH).
- `raaf` — a specific physical box (mirrors the same host in `fedora-desktop`).
- `remote` — not a fixed machine; a generic placeholder host used when configuring *some* new/different
  desktop machine from the current one.

## Layout

- `pyinfra/deploy.py` — the main entrypoint. Plain `import modules.X` statements (with a
  `# pyright: ignore` comment each, since Pylance flags them as unused) — see "Module self-invocation"
  below for why.
- `pyinfra/modules/*.py` — one file per feature/tool, each exposing a single `@deploy`-decorated
  `deploy_x()` function **and calling it unconditionally at the bottom of the file** — equivalent to
  `fedora-desktop/ansible/tasks/*.yml`.
- `pyinfra/group_data/all.py` — shared vars (username, package lists, tool versions). Per-host overrides
  live in `pyinfra/group_data/<host>.py`.
- `pyinfra/files/` — static files pushed to machines (dotfiles, configs). `pyinfra/templates/` — Jinja2
  templates rendered via `files.template`.
- `pyinfra/modules/desktop/` — swappable per-desktop-environment module, dispatched on
  `group_data.desktop_environment`. Currently placeholders (Cinnamon/KDE/Xfce) — the target DE isn't
  finalized yet.
- `inspec/mint-desktop/` — Inspec/Cinc Auditor controls that verify the deploy actually configured the
  machine correctly. Run locally against `localhost` with `./test-local.sh`, or against a remote host
  with `./test-remote.sh <inventory-group>` (e.g. `remote`, `raaf`) — both are thin wrappers around
  `run-test.py`, which reuses `pyinfra/inventory.py`'s own connection data (no separate secret lookup).
- `setup-repo.sh` — one-time repo bootstrap: symlinks `pyinfra/secrets_data.py` from `../desktop-secrets`.
- `prepare.sh` — bootstraps pyinfra itself on a fresh box (creates `~/python3-venv/pyinfra-latest`,
  installs `requirements.txt` into it) before the deploy can run.
- `check.sh` — runs everything CI runs (pyright, unit tests, Inspec profile check). Single source of
  truth: `.github/workflows/ci.yml` just calls this, so it's always runnable locally before pushing.

## CI (`.github/workflows/ci.yml`)

One job that installs `cinc-auditor` + `requirements.txt` then runs `./check.sh` (pyright type-check
against `pyinfra/`, `unittest` on `pyinfra/tests/`, and an Inspec profile syntax check). No linter:
ansible-lint has no direct pyinfra equivalent, and ruff was deliberately left out. A separate
`secrets-detection.yml` workflow scans pushes for leaked secrets (Gitleaks, TruffleHog, detect-secrets),
matching `fedora-desktop`. `.secrets.baseline` was seeded from an initial `detect-secrets scan` — the
handful of "Secret Keyword" hits in `vault.py`/`test_vault.py`/this file are variable-name false
positives (`VAULT_PASSWORD` etc), not real secrets.

## Known pyinfra gotchas (found the hard way, verified against a real Mint VM)

- **`config.py`'s bare `SUDO = True` does nothing.** pyinfra's CLI `exec()`s `config.py` and discards its
  locals entirely. You must mutate the live config object: `from pyinfra.context import config;
  config.SUDO = True`. Same applies to `host`/`deploy`/`config` imports generally — `from pyinfra import
  host` triggers Pylance's "not exported" warning and should be `from pyinfra.context import host`
  (and `from pyinfra.api.deploy import deploy`, not `from pyinfra.api import deploy`).
- **Module self-invocation.** Pointing pyinfra at a module file (`pyinfra inventory.py modules/git.py`)
  only *executes* module-level code — a `@deploy`-decorated function that's merely defined, never called,
  does nothing. Every module therefore calls its own `deploy_x()` unconditionally at the bottom of the
  file. `deploy.py` then just does plain `import modules.x` for each one (relying on Python's
  import-executes-top-level-code behavior) rather than importing-and-calling the functions itself,
  because pyinfra's CLI natively accepts multiple deploy files as separate positional args
  (`pyinfra inventory.py modules/git.py modules/ssh.py`) — **that's the real `--tags` equivalent**, not
  a `--data`-driven conditional hack.
- **`git.config` keys must be lowercase.** Git normalizes config variable names to lowercase in its own
  storage, and the `GitConfig` fact reads them back that way. `core.fileMode` (mixed case) never matches
  `core.filemode` (what git actually stores), so it reports "changed" on every run even though nothing
  changed.
- **`files.line` needs both `escape_regex_characters=True` *and* `extended_regex=True` together**, or not
  at all. `escape_regex_characters=True` escapes `()[]{}` assuming POSIX *extended*-regex semantics
  (escaped = literal). The underlying `grep` defaults to *basic*-regex mode, where `\(` `\)` `\{` `\}` mean
  the opposite (grouping/interval operators). Pairing them wrong silently breaks the presence-check and
  the line gets re-appended every run.
- **`Command` fact returns `None`, not `""`,** when the command produces zero output lines (e.g. checking
  a not-yet-installed binary's `--version`). Guard with `if result and ...`, not just `if result...` when
  membership-testing a substring — `"x" in None` raises `TypeError`.
- **`files.unarchive` needs an explicit `creates=` path for idempotency** — it's not automatic. Without it
  every run re-extracts.
- **`files.put` only compares content against regular files.** Against a symlink (e.g.
  `/etc/default/locale` → `../locale.conf` on this systemd-style Mint layout, vs. a plain file on Fedora)
  it always takes the unconditional-overwrite path. Write to the real underlying file instead.
- **Don't trust Fedora/dnf package names when translating to apt.** `samba-client` doesn't exist on
  Debian/Ubuntu/Mint — the real package is `smbclient`. `apt-get install <nonexistent-name>` did not
  reliably error either, it's worth explicitly checking `apt-cache policy <name>` when porting a package
  list rather than assuming a name carries over.
- **Pylance's `reportUnusedImport` needs `# pyright: ignore`, not `# noqa`** — the latter is a Ruff/Flake8
  convention pyright doesn't recognize. This repo doesn't run ruff, so only the pyright form is used.
- **`privy` ships no type stubs** (no `py.typed`, no bundled `.pyi`). Local stubs live in
  `typings/privy/`, hand-annotated (Pylance's auto-generated stub skeletons have no real type
  annotations, just comments). The stub package's `__init__.py` re-exports must use redundant aliasing
  (`from privy.core import hide as hide`), or pyright treats them as private/non-re-exported — a classic
  stub-file pitfall, not specific to `privy`.

## Conventions

- One module file per feature under `pyinfra/modules/`, following the pattern above — mirrors
  `fedora-desktop`'s one-task-file-per-feature pattern via `import_tasks`.
- **TDD**: when adding a new tool/feature, write the failing Inspec/Cinc Auditor control(s) in
  `inspec/mint-desktop/controls/` first (commented out is fine as a placeholder until the module exists),
  confirm they fail, then write the pyinfra operations to make them pass. Verify idempotency by running
  the module twice against a real target (`./test-remote.sh <group>` + the module file directly, e.g.
  `pyinfra inventory.py modules/git.py --limit remote`) — a clean "No Change" on the second run is the
  actual bar, not just "no errors on the first run".
