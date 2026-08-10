#!/home/sebastiaan/python3-venv/pyinfra-latest/bin/python3
"""Run the Inspec/Cinc Auditor profile against localhost or a remote host, reusing the
same connection data pyinfra itself uses (pyinfra/inventory.py) - no separate secret
lookup. Used by test-local.sh and test-remote.sh; not normally run directly.

Usage: ./_run-test.py <inventory-group> [tag]
    # e.g. localhost, mint_vm, dell_laptop, raaf
    # optional tag, e.g. tools -> runs only controls tagged :tools (see inspec/mint-desktop/controls/*.rb)
"""

import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
PROFILE_DIR = REPO_DIR / "inspec" / "mint-desktop"
sys.path.insert(0, str(REPO_DIR / "pyinfra"))


def main() -> None:
    if len(sys.argv) not in (2, 3):
        sys.exit(
            f"Usage: {sys.argv[0]} <inventory-group> [tag]  "
            "(e.g. localhost, mint_vm, dell_laptop, raaf; optional tag e.g. tools)"
        )
    group_name = sys.argv[1]

    cmd: list[str] = [
        "cinc-auditor", "exec", str(PROFILE_DIR),
        "--chef-license=accept-silent", "--auto-install-gems",
    ]

    # Always runs the whole profile directory, never a single controls/*.rb file directly - an
    # ad hoc single-file LOCATIONS run drops inspec.yml's profile-level inputs (e.g.
    # `username`), breaking every control that calls input(...). --tags filters the *results*
    # down instead, matched against each control's own `tag :<name>` (every control in
    # controls/<name>.rb carries that tag) - the InSpec-idiomatic way to select a subset,
    # unlike reconstructing a title regex: control titles aren't unique/stable enough for that
    # (confirmed live - system.rb's "user is in #{grp} group" loosely regex-matched tools.rb's
    # unrelated "user is in the docker group" when tried that way).
    if len(sys.argv) == 3:
        cmd += ["--tags", sys.argv[2]]

    if group_name == "localhost":
        pass  # cinc-auditor defaults to local execution with no -t flag
    else:
        import inventory

        group = getattr(inventory, group_name, None)
        if not group:
            sys.exit(f"No such inventory group in pyinfra/inventory.py: {group_name}")

        hostname, data = group[0]
        ssh_hostname = str(data.get("ssh_hostname", hostname))
        ssh_user = str(data.get("ssh_user"))
        ssh_password = data.get("ssh_password")

        if not ssh_password:
            sys.exit(f"No ssh_password configured for inventory group {group_name!r}")

        cmd += [
            "-t", f"ssh://{ssh_user}@{ssh_hostname}",
            "--password", str(ssh_password),
        ]

    result = subprocess.run(cmd, cwd=REPO_DIR)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
