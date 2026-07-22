#!/home/sebastiaan/python3-venv/pyinfra-latest/bin/python3
"""Run the Inspec/Cinc Auditor profile against localhost or a remote host, reusing the
same connection data pyinfra itself uses (pyinfra/inventory.py) - no separate secret
lookup. Used by test-local.sh and test-remote.sh; not normally run directly.

Usage: ./run-test.py <inventory-group>   # e.g. localhost, mint_vm, dell_laptop, raaf
"""

import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_DIR / "pyinfra"))


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <inventory-group>  (e.g. localhost, mint_vm, dell_laptop, raaf)")
    group_name = sys.argv[1]

    cmd: list[str] = [
        "cinc-auditor", "exec", "inspec/mint-desktop",
        "--chef-license=accept-silent", "--auto-install-gems",
    ]

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
