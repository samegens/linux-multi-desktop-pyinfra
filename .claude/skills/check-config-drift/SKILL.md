---
name: check-config-drift
description: Compare live config/settings on this machine (localhost) against what mint-desktop's pyinfra modules would deploy, and offer to port each drifted setting back into the repo. Use when the user asks to check for config drift, sync settings back to the repo, or "did I tweak anything I forgot to commit."
---

# Check config drift

This machine (`localhost`) is deployed from this repo, but the user routinely hand-tweaks
settings on the live machine (dotfiles, app configs, dconf settings, git config) and forgets to
port the change back. This skill finds those drifts and, one at a time, asks whether to bring
each one into the repo.

Read `manifest.md` in this skill's directory first — it is the authoritative, maintained list of
every checkable setting, grouped by *kind* (file / generated / keyvalue / dconf / git-config),
with the live location, the repo source, and per-item notes about expected noise. Don't try to
rediscover this list from the module source each run — the manifest is kept in sync with the
modules as a project convention (see CLAUDE.md's "Conventions" section); trust it, but if a
module referenced in the manifest no longer exists, or a live path is missing entirely (feature
never installed on this machine), skip that row and say so rather than erroring.

## Procedure

1. **Read the manifest fully.**

2. **Walk every row, grouped by kind**, reading the live value the row specifies:
   - `file`: `Read` the live file and the repo file, diff them.
   - `generated`: `Read` the live file; re-derive what the module would currently write by
     reading the relevant constant/dict directly out of the module's `.py` source (don't guess —
     read the actual current source, it may have changed since the manifest note was written).
     Compare per the row's specific comparison rule (e.g. bashrc.py: line-presence, not whole-file).
   - `keyvalue`: read the live file, extract only the listed keys, compare against the module's
     dict.
   - `dconf`: run the read command (`dconf read <path>` / `gsettings get ...` / `localectl
     status`) via Bash, compare to the module's constant.
   - `git-config`: run `git config --global --get <key>` via Bash, compare to the module's dict
     (skip `user.name`/`user.email` per the manifest note).

   Batch independent reads/commands in parallel where possible — there's no dependency between
   rows.

3. **Build a list of actual drifts** — live value differs from what the repo currently encodes.
   Silently skip rows that match (no need to report "no change"). For `session.ini`-style noisy
   rows, apply the manifest's own guidance about what counts as a real candidate vs. session
   noise before including it.

4. **Present drifts one at a time** (or a few at a time if clearly related, e.g. several new
   `.bashrc` aliases at once), each with a concrete before/after (repo value vs. live value), and
   ask via `AskUserQuestion` whether to port it into the repo. Don't dump the whole list and ask
   one blanket yes/no — each row is an independent decision.

5. **For each accepted change**, edit the repo:
   - `file` kind: copy the live file's content into the `files/...` repo path (`Edit`/`Write`).
   - `generated`/`keyvalue` kind: edit the module's Python source (the dict/template constant),
     not a `files/` file — there is no static file backing these.
   - `dconf`/`git-config` kind: same — edit the module's dict constant to the new value.

   Don't touch anything for a row the user declines.

6. **After processing all drifts**, summarize what was changed (or that nothing had drifted) in
   1-2 sentences. Don't commit — leave that decision to the user.

## Scope reminder

Package/flatpak/VS Code-extension *lists* are out of scope (see manifest.md's intro) — this
skill is about config content, not software inventory. Don't wander into checking whether new
apt packages or flatpaks are installed.
