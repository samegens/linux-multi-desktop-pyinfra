# mint-desktop

pyinfra deploy that automates Sebastiaan's Linux desktop setup and configuration, targeting both
Linux Mint (apt) and Fedora (dnf) from a single codebase — see "Multi-distro support" below.
Rebuilt from [`../fedora-desktop`](../fedora-desktop) (Ansible, Fedora KDE) using pyinfra instead
of Ansible — same spirit and conventions where they still apply. **Lean core** rebuild, not a full
1:1 port; see "Scope" in README.md for what's deliberately not ported yet.

## Secrets model

`../desktop-secrets` (sibling dir) holds `secrets_data.py`: `privy`-encrypted string constants,
shared with other repos. `pyinfra/secrets_data.py` is a **symlink** into it, created by
`setup-repo.sh` — gitignored, doesn't exist in a fresh checkout/CI (`typings/secrets_data.pyi` is a
hand-written stub so pyright still type-checks). `pyinfra/vault.py`'s `reveal(hidden: str) ->
bytes` decrypts using `$VAULT_PASSWORD` env var → `~/Dropbox/ansible/.vault_pass` (shared with
`fedora-desktop`), fails loudly if neither is set. Not named `secrets.py` (would shadow stdlib).
`inventory.py`'s `_ssh_and_sudo_password = vault.reveal(...)` is reused for both `remote`/`raaf`'s
SSH login and `localhost`'s local sudo (same real password). `.gitleaks.toml`/`.secrets.baseline` +
`secrets-detection.yml` catch leaks — don't bypass them.

## Run modes

Same deploy (`pyinfra/deploy.py`) targets `localhost` (`@local`, reconfigure this machine) or
`remote`/`raaf` (SSH to a different machine):

```bash
cd pyinfra && /home/sebastiaan/python3-venv/pyinfra-latest/bin/pyinfra inventory.py deploy.py --limit <group> -y
```

Wrapper scripts (`run.sh`/`run-local.sh`, tee output to a timestamped log) are **planned, not yet
built** — don't assume they exist.

## Verification targets

- **`remote`** — disposable Mint test VM, `192.168.149.134` (IP may change — ask the user if
  unreachable). Credentials: `secrets_data.SSH_PASSWORD`.
- **`localhost`** — this dev machine (Fedora). Real, non-disposable — every run has real effects.
  Goal: eventually replace the user's Ansible-based `../fedora-desktop` with this repo here.
- **`raaf`** — real physical box, `Distro.UBUNTU`, not a verification target — just proves the
  package-manager abstraction generalizes to a third distro for free.

**Per-module dev loop** (one module at a time):

1. Write/port `pyinfra/modules/x.py`. Route any apt/dnf-specific fact through
   `pkgmgr.py`/`services.py`/`paths.py` — `modules/*.py` itself must never branch on
   `host.data.distro`.
2. Preview: `pyinfra inventory.py modules/x.py --limit <group>` **without** `-y` shows a real
   "Detected changes" table then prompts — the actual `--check` equivalent. (`-y` disables change
   detection entirely per its own `--help` text; `--dry` alone shows nothing useful.)
3. Run for real (`-y`) against **both** `remote` and `localhost`; run again — everything must show
   "No Change" on the second run or it's a real idempotency bug.
4. Add/update Inspec controls (`inspec/mint-desktop/controls/*.rb`) — prefer testing observable
   *behavior* over config-file syntax where the distros' native tooling differs (e.g.
   `command('localectl status')`, not a regex on `/etc/locale.conf`), so one control stays correct
   on both without a conditional inside it. Confirm via `./test-remote.sh remote` + `./test-local.sh`.
5. Add `import modules.x  # pyright: ignore` to `deploy.py`; update README's "Scope" section.

## Multi-distro support (Mint/apt + Fedora/dnf)

`pkgmgr.py` owns `Distro → PackageManager` — the *only* place that switches on `Distro` directly.
Everything else dispatches on `PackageManager` instead, so a distro sharing an existing package
manager (e.g. `Distro.UBUNTU`, already added for `raaf`) is a one-line addition to
`DISTRO_PACKAGE_MANAGERS`. `PackageManager` means "packaging ecosystem" (Debian's apt archives vs
Fedora/RHEL's dnf/rpm archives), not "which CLI binary runs install" — package names, systemd unit
names, and packaged config-file paths are all baked into the package as built for a given archive,
so any distro pulling from the same archive shares the same answer (confirmed empirically, not
assumed — see gotchas).

- `pkgmgr.py`: `get_distro()`, `get_package_manager()`, `install()`, `update_cache()`,
  `PACKAGE_NAME_OVERRIDES` (verify against `dnf info`/`apt-cache policy` or `../fedora-desktop`'s
  working Ansible before adding — never guess), `ensure_en_us_locale()`, `get_en_us_locale_content()`.
- `services.py`: `Service` enum + `get_service_name()` (e.g. `ssh`/`sshd`).
- `paths.py`: `SystemPath` enum + `get_system_path()` (e.g. `/etc/bash.bashrc`/`/etc/bashrc`).
- All fail loudly (`ValueError`) if `host.data.distro` is unset — every host needs `distro` set in
  its `group_data/<host>.py`. `all.py`'s `distro = None` default makes that failure clean instead
  of an opaque `AttributeError` (same pattern as `desktop_environment = None`).
- Not named `distro.py`: pyinfra depends on the third-party `distro` PyPI package; a local
  `pyinfra/distro.py` would shadow it.

## Current status

README.md's **Scope** section is the source of truth for ported vs. deferred — keep it in sync.
Done and verified (idempotent + Inspec-covered, both Mint and Fedora): `base`, `git`, `ssh`,
`bashrc`, `starship`, `go`, `rust`, `vscode` (editor, extensions, config files - PowerShell/.NET
SDK deliberately excluded, see `pyinfra/modules/vscode.py`'s docstring for the Fedora/Microsoft
dotnet-sdk-8.0 package name collision that made it too risky for this pass), `python_venv`
(`~/python3-venv/*`, data-driven `VENVS` dict in `pyinfra/modules/python_venv.py` - ported all
four venvs from `fedora-desktop/ansible/tasks/python-venv.yml`, not just this repo's own
pyinfra-latest. Note: pyinfra's `pip.packages` is only idempotent for `==`-pinned versions - a
`<`/`<=`/`>`/`>=` spec makes it look up the literal spec version against what's installed, never
matches, and reinstalls every run; confirmed live against `remote`. Use an exact pin instead),
`cinc_auditor` (branches on `PackageManager` directly like `vscode.py`, since
downloads.cinc.sh has no distro repo - just a pinned-version rpm/deb per release. Also ports the
docker-resource deprecation-regex fix from `fedora-desktop`'s Ansible task, and derives the apt
side's Ubuntu release from a live fact rather than a hardcoded `group_data` var - a hardcoded
`ubuntu_release = "22.04"` had gone stale unnoticed; Mint 22.3's `remote` VM actually reports
`UBUNTU_CODENAME=noble` i.e. 24.04, see `pkgmgr.get_ubuntu_release()`'s docstring), `docker`
(Engine + Compose plugin from Docker's own apt/dnf repo, not docker.io/moby-engine; apt side uses
`pkgmgr.get_ubuntu_codename()` since Docker has no Mint archive. Two gotchas: `apt.update()`
after adding a repo must be gated behind a repo-file-exists check, it has no idempotency of its
own; on Fedora, dnf's Provides matching makes legacy package "docker" falsely match the already-
installed docker-ce, so the old-package cleanup is gated behind "docker not yet installed").

**Next up**, one module + Inspec control at a time via the dev loop above — verify Fedora
immediately after Mint each time, don't leave a module Mint-only: `nodejs`,
`desktop` placeholder, then a dedicated PowerShell/.NET SDK
module (split out of `vscode.py` - needs section-aware edits to Fedora's own
`fedora.repo`/`fedora-updates.repo` to resolve the `dotnet-sdk-8.0` name collision, not the
global-exclude approach that broke installs under dnf5). Wrapper scripts also outstanding.
`k3s` added to the end of this queue (developer/k3s-experiment-station goal) once the above land.

## Layout

- `pyinfra/deploy.py` — entrypoint, plain `import modules.X  # pyright: ignore` per module (each
  module self-invokes `deploy_x()` at the bottom — see gotchas for why).
- `pyinfra/modules/*.py` — one file per feature, mirrors `fedora-desktop/ansible/tasks/*.yml`.
- `pyinfra/pkgmgr.py`, `services.py`, `paths.py` — multi-distro abstraction (see above), plain
  shared modules at `pyinfra/` root alongside `vault.py`, not under `modules/`.
- `pyinfra/group_data/all.py` — shared vars; per-host overrides in `group_data/<host>.py`.
- `pyinfra/modules/desktop/` — swappable per-DE module, dispatched on
  `group_data.desktop_environment`. Still just a planned placeholder — directory doesn't exist yet.
- `inspec/mint-desktop/` — controls; `./test-local.sh` / `./test-remote.sh <group>`.
- `setup-repo.sh` — symlinks `secrets_data.py`. `prepare.sh` — bootstraps the pyinfra venv.
- `check.sh` — runs everything CI runs (pyright, unit tests, Inspec syntax check); source of truth
  for `.github/workflows/ci.yml`.

## CI

`ci.yml` and `secrets-detection.yml` both run on push/PR **and** nightly (`schedule:` cron, to
catch breakage from unpinned/updated tooling independent of code changes) — README badges use
`?event=push`/`?event=schedule` on the same 2 files rather than separate nightly workflows.

## Known pyinfra gotchas (verified against real Mint + Fedora targets)

- **`config.py`'s bare `SUDO = True` does nothing** — pyinfra's CLI discards `config.py`'s locals.
  Mutate the live object: `from pyinfra.context import config; config.SUDO = True`. Same for
  `host`/`deploy` imports — `from pyinfra.context import host`, `from pyinfra.api.deploy import deploy`.
- **Module self-invocation**: a `@deploy`-decorated function that's merely defined, never called,
  does nothing when pyinfra loads the file — every module calls its own `deploy_x()`
  unconditionally at the bottom. `deploy.py` then just imports each module for its side effect.
- **`git.config` keys must be lowercase** — git normalizes storage, so mixed-case keys never match
  and report "changed" every run.
- **`files.line` needs both `escape_regex_characters=True` *and* `extended_regex=True` together**,
  or the presence-check silently breaks and the line re-appends every run.
- **`Command` fact returns `None`, not `""`,** on zero output lines — guard with `if result and
  ...`, not just `if result...`.
- **`files.unarchive` needs an explicit `creates=`** for idempotency — not automatic.
- **`files.put` only compares content against regular files, not symlinks** (e.g. Mint's
  `/etc/default/locale` → `../locale.conf`) — write the real underlying file instead.
  `/etc/locale.conf` is Fedora's native (non-symlinked) file too, so only the *content* needs to
  differ by package manager (`pkgmgr.get_en_us_locale_content()`), not the destination.
- **Package names don't carry over between apt and dnf, in either direction** — confirmed:
  `samba-client`/`smbclient`, `ImageMagick`(!)/`imagemagick`, `powerline-fonts`/`fonts-powerline`.
  Neither manager reliably errors on a nonexistent name — check `dnf info`/`apt-cache policy`, or
  cross-check `../fedora-desktop`'s working Ansible task first.
- **`dnf.update()` is NOT the dnf analog of `apt.update()`** — it's a full `dnf update -y` system
  upgrade, not a cache refresh (dnf refreshes metadata on every install anyway). Never wire it into
  `pkgmgr.update_cache()`'s dnf branch "by analogy" — on `localhost`, a real machine, that would
  trigger an unintended full-system upgrade.
- **InSpec's `os.redhat?` is not true for Fedora** (`cinc-auditor detect` confirms Fedora's family
  is `['fedora', ...]`, no `'redhat'` entry — Train reserves that for RHEL-downstream distros).
  Use `os.debian?` for the Mint/Ubuntu side.
- **`-y` disables pyinfra's own change-detection preview**, and `--dry` alone doesn't restore it
  (`--dry -y` together shows nothing useful). Run **without** `-y` for a real "Detected changes"
  table + prompt — the actual `--check` equivalent.
- **A package's presence isn't the same fact as whether what it provides is already true.** Found
  on Fedora: `glibc-langpack-en` wasn't installed, but `locale -a` already listed (and confirmed
  functional) `en_US.utf8`, generated some other way. Check the actual behavior first
  (`pkgmgr.ensure_en_us_locale()`'s pattern) before falling through to a package-manager-specific
  fix mechanism — same principle for Inspec controls (behavior over presence).
- **CI can fail on things that work locally without you noticing** — `check.sh`'s `PYTHON` var
  must be an absolute path before `--pythonpath` (CI overrides it to bare `python3`, which pyright
  silently can't resolve, hiding every installed package). If a CI-only failure looks bizarre,
  reproduce with a clean venv + the exact CI env override rather than trusting local `./check.sh`.
- **`privy`/`secrets_data` have hand-written stubs in `typings/`** (upstream `privy` ships none;
  `secrets_data` doesn't exist in a fresh checkout). Re-exports need redundant aliasing (`from X
  import y as y`) or pyright treats them as private. Pylance's unused-import warning needs `#
  pyright: ignore`, not `# noqa` (this repo doesn't run ruff).

## Conventions

- One module file per feature, mirrors `fedora-desktop`'s one-task-file-per-feature pattern.
- **TDD**: write the failing Inspec control first (commented out as a placeholder is fine until the
  module exists), confirm it fails, then write the pyinfra operations to make it pass. A clean "No
  Change" on the *second* run against a real target is the actual idempotency bar — see
  "Verification targets" above for the full dev loop.
