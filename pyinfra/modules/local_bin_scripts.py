"""Personal wrapper scripts under ~/.local/bin, keyed by filename -> source in files/local_bin.
Data-driven like python_venv.py's VENVS dict, so a new personal script is a one-line addition.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files

SCRIPTS = [
    "cl.sh",
    "analyze-network.sh"
]

@deploy("Personal ~/.local/bin scripts")
def deploy_local_bin_scripts():
    username = host.data.username
    bin_dir = f"/home/{username}/.local/bin"

    files.directory(
        name="Create ~/.local/bin",
        path=bin_dir,
        user=username,
        group=username,
        mode="755",
        _sudo=False,
    )

    for script in SCRIPTS:
        files.put(
            name=f"Copy {script} into ~/.local/bin",
            src=f"files/local_bin/{script}",
            dest=f"{bin_dir}/{script}",
            user=username,
            group=username,
            mode="755",
            _sudo=False,
        )

deploy_local_bin_scripts()
