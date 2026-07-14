"""Entrypoint. Runs every module in order.

Each module calls its own deploy_*() at the bottom, so pyinfra also accepts a subset of
module files directly as separate CLI args instead of this file - that's the native
--tags equivalent:
    pyinfra inventory.py modules/git.py modules/ssh.py --limit localhost
"""

import modules.base  # noqa: F401
import modules.git  # noqa: F401
import modules.ssh  # noqa: F401
import modules.bashrc  # noqa: F401
import modules.starship  # noqa: F401
