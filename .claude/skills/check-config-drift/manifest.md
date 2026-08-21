# Config drift manifest

Every place on `localhost` where this repo writes a setting that the user could plausibly
hand-tweak afterwards and forget to port back. `check-config-drift` walks this list top to
bottom. Each row: how to read the **live** value, what the **repo** currently says, and where
to write a fix if the user wants the live value ported back.

Package/flatpak/VS Code extension *lists* (`group_data/all.py`'s `packages`, `flatpaks`,
`vscode_extensions`) are deliberately **out of scope** — this manifest only covers config
*content*, not software inventory.

## Kind: file (repo file byte-diff against live file, verbatim copy)

| # | Module | Live path | Repo source | Notes |
|---|--------|-----------|--------------|-------|
| 1 | starship.py | `/etc/starship.toml` | `pyinfra/files/etc/starship.toml` | |
| 2 | vscode.py | `~/.config/Code/User/keybindings.json` | `pyinfra/files/vscode/keybindings.json` | |
| 3 | vscode.py | `~/.config/Code/User/settings.json` | `pyinfra/files/vscode/settings.json` | |
| 4 | vscode.py | `~/.config/Code/User/snippets/csharp.json` | `pyinfra/files/vscode/snippets/csharp.json` | |
| 5 | doublecmd.py | `~/.config/doublecmd/doublecmd.xml` | `pyinfra/files/doublecmd/doublecmd.xml` | |
| 6 | doublecmd.py | `~/.config/doublecmd/multiarc.ini` | `pyinfra/files/doublecmd/multiarc.ini` | |
| 7 | doublecmd.py | `~/.config/doublecmd/shortcuts.scf` | `pyinfra/files/doublecmd/shortcuts.scf` | |
| 8 | doublecmd.py | `~/.config/doublecmd/localconfig.xml` | `pyinfra/files/doublecmd/localconfig.xml` | Holds the saved hotdir list (`DirectoryHotList`) as of Double Commander 1.2.x — it used to live inside `doublecmd.xml` on 1.1.x, moved here on upgrade. `~/.config/doublecmd/session.ini` was dropped from this manifest and from `CONFIG_FILES` — it's pure window/session state (open tabs, last paths, geometry), never a deliberate setting; confirmed nothing worth tracking in it. |

## Kind: generated (module renders content from a Python template/dict — compare live file
against what the template *would* currently produce; a fix means editing the module's source,
not a `files/` file)

| # | Module | Live path | Repo source | Notes |
|---|--------|-----------|--------------|-------|
| 9 | bashrc.py | `~/.bashrc` | `pyinfra/modules/bashrc.py`'s `aliases` dict + the Cargo `PATH` line | Only check whether each dict entry's line is still present in the live file, and whether the live file has *new* alias-shaped lines (`alias x=...` or simple shell functions) not in the dict — full-file diff would be noisy since `.bashrc` also carries distro/desktop-added boilerplate this repo doesn't own. |
| 10 | bashrc.py | `~/.inputrc` | `pyinfra/modules/bashrc.py`'s `StringIO(...)` content | Whole-file diff is fine here — this repo owns the entire file. |
| 11 | go.py | `/etc/profile.d/go.sh` | `pyinfra/modules/go.py`'s `StringIO(...)` content | Low churn expected. |
| 12 | obsidian.py | `~/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json` | `pyinfra/modules/obsidian.py`'s `OBSIDIAN_CONFIG_TEMPLATE` | Real Obsidian config grows extra keys (recent files, plugin state) the template doesn't set — only check whether the `vaults` entry (path) still matches; ignore everything else in the JSON. |
| 13 | workrave.py | `~/.config/autostart/workrave.desktop` | `pyinfra/modules/workrave.py`'s `AUTOSTART_DESKTOP_ENTRY` | Low churn expected. |
| 14 | starship.py | System bashrc's `# {mark} PYINFRA MANAGED BLOCK - STARSHIP` block (path via `paths.get_system_path(SystemPath.SYSTEM_BASHRC)`) | `pyinfra/modules/starship.py`'s `files.block(content=...)` | Low churn expected. |

## Kind: keyvalue (module pins only specific `key=value` lines inside an otherwise
upstream-owned config file, via `keyfile.set_key_value` — only check those exact keys, never
the surrounding file)

| # | Module | Live path | Repo source | Notes |
|---|--------|-----------|--------------|-------|
| 15 | darktable.py | `~/.var/app/org.darktable.Darktable/config/darktable/darktablerc` | `pyinfra/modules/darktable.py`'s `DARKTABLERC_SETTINGS` dict | Check each key's live value against the dict; also worth a quick look for other settings the user may have changed near those keys, but don't treat every other line in the file as a candidate — the module's own docstring explains why (session/window state noise). |
| 16 | ghostty.py | `~/.config/ghostty/config.ghostty` | `pyinfra/modules/ghostty.py`'s `GHOSTTY_CONFIG_SETTINGS` dict | Same pattern. Ghostty's config file may have many more lines the user added by hand (theme, font, keybinds) — those are candidates to promote into `GHOSTTY_CONFIG_SETTINGS`, not just the pinned key. |

## Kind: dconf (GSettings/dconf key, read via `dconf read <path>` or `gsettings get`, no file
involved)

| # | Module | Live key | Repo source | Notes |
|---|--------|----------|--------------|-------|
| 17 | workrave.py | `/org/workrave/<key>` for each key in `DCONF_SETTINGS` | `pyinfra/modules/workrave.py`'s `DCONF_SETTINGS` dict | Read with `dconf read /org/workrave/<key>`. |
| 18 | keyboard.py | Compose-key XKB option (Cinnamon: `gsettings get org.cinnamon.desktop.input-sources xkb-options`; dnf: `localectl status`'s `X11 Options` line) | `pyinfra/modules/keyboard.py`'s `COMPOSE_OPTION` constant | Binary present/absent check, not really "tweakable" beyond on/off — low priority. |

## Kind: git-config (global git config values)

| # | Module | Live command | Repo source | Notes |
|---|--------|--------------|--------------|-------|
| 19 | git.py | `git config --global --get <key>` for `core.filemode`, `push.autosetupremote`, `init.defaultbranch`, `push.default` | `pyinfra/modules/git.py`'s `config` dict | `user.name`/`user.email` are identity, not tweakable settings — skip those two keys. |

## Adding a new row

See CLAUDE.md's "Conventions" section — every new module gets checked at write-time for
whether it belongs here, not left for someone to notice later.
