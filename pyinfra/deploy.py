"""Entrypoint. Runs every module in order.

Each module calls its own deploy_*() at the bottom, so pyinfra also accepts a subset of
module files directly as separate CLI args instead of this file - that's the native
--tags equivalent:
    pyinfra inventory.py modules/git.py modules/ssh.py --limit localhost
"""

# pyright: ignore suppresses Pylance's unused-import warning - these are intentional
# side-effect imports (each module deploys itself on import).
import modules.base  # pyright: ignore
import modules.git  # pyright: ignore
import modules.ssh  # pyright: ignore
import modules.bashrc  # pyright: ignore
import modules.starship  # pyright: ignore
import modules.go  # pyright: ignore
import modules.rust  # pyright: ignore
import modules.vscode  # pyright: ignore
import modules.python_venv  # pyright: ignore
import modules.cinc_auditor  # pyright: ignore
import modules.docker  # pyright: ignore
import modules.k3s  # pyright: ignore
import modules.firefox  # pyright: ignore
import modules.doublecmd  # pyright: ignore
import modules.workrave  # pyright: ignore
