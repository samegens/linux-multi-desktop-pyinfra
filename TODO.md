# TODO

Known idempotency bugs, found live against `mint_vm` (2026-09-08) via a full `all.py -y` run
repeated twice - unrelated to any in-progress work at the time, just surfaced along the way.

- **`~/.config/autostart` mode conflict** - `pyinfra/modules/base.py`'s bulk directory-creation
  loop (around line 33) creates it with `mode="775"` (falls into that loop's generic
  `else` branch, since it's only special-cased for `path == ".config"`), while
  `pyinfra/modules/workrave.py`'s `_install_autostart_entry()` (around line 47) creates the same
  directory with `mode="755"`. Two operations targeting the identical path with different
  desired modes - confirmed live: they alternate "Success" forever across repeated `-y` runs,
  each one "correcting" the mode the other just set, never reaching a stable "No Change". Likely
  fix: drop `.config/autostart` from `base.py`'s loop and let `workrave.py` own it exclusively,
  since `workrave.py` is the one that actually cares about that directory's permissions.

- **Claude Code reinstalls every run** - `pyinfra/modules/claude_code.py`'s "Install Claude
  Code" operation showed "Success" (not "No Change") on every one of several consecutive `-y`
  runs against `mint_vm`. Not yet root-caused - needs investigation into why its idempotency
  check never reports the binary as already present/current.

- **Report the `files.block` SELinux context bug upstream** - found while writing
  `pyinfra/modules/hosts.py` (2026-09-08): `files.block()` silently drops a file's SELinux
  context (replaces it with the temp dir's default, e.g. `net_conf_t` -> `user_tmp_t` for
  `/etc/hosts`), confirmed live via `systemd-resolved` AVC denials on `localhost`; `hosts.py`
  now works around it with a Fedora-only `restorecon` follow-up. Root cause, minimal repro, and
  a proposed fix are written up in
  `/home/sebastiaan/git/pyinfra-files.block-selinux-context-bug` (a separate repo, not a sibling
  of this one) - still needs to actually be filed as a GitHub issue against `pyinfra-dev/pyinfra`
  (confirmed via search: no existing issue covers this; #1119 is related but distinct - same
  code path, different symptom).
