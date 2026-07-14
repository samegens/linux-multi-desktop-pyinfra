"""Git install + global config."""

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.operations import apt, git


@deploy("Configure git")
def deploy_git():
    apt.packages(name="Install git", packages=["git"], present=True)

    config = {
        "user.name": host.data.git_user_name,
        "user.email": host.data.git_user_email,
        "core.fileMode": "true",
        "push.autoSetupRemote": "true",
        "init.defaultBranch": "main",
        "push.default": "current",
    }
    for key, value in config.items():
        git.config(
            name=f"Set git {key}",
            key=key,
            value=value,
            _sudo=False,
        )
