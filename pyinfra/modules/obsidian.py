"""Obsidian - flatpak note-taking app config.

Package itself (md.obsidian.Obsidian) is installed by base.py via host.data.flatpaks; this module
only seeds its config so it opens the notes vault by default.
"""

from io import StringIO

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files

OBSIDIAN_CONFIG_TEMPLATE = (
    '{{"vaults":{{"f94871e3c3aa89ca":{{"path":"/home/{username}/Dropbox/projects/Obsidian/notes",'
    '"ts":1720502347936,"open":true}}}}}}'
)

@deploy("Configure Obsidian")
def deploy_obsidian():
    username = host.data.username
    config_dir = f"/home/{username}/.var/app/md.obsidian.Obsidian/config/obsidian"

    files.directory(
        name="Create Obsidian config directory",
        path=config_dir,
        user=username,
        group=username,
        mode="700",
        _sudo=False,
    )
    files.put(
        name="Create Obsidian config",
        src=StringIO(OBSIDIAN_CONFIG_TEMPLATE.format(username=username)),
        dest=f"{config_dir}/obsidian.json",
        user=username,
        group=username,
        mode="644",
        _sudo=False,
    )

deploy_obsidian()
