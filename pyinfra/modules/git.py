"""Git install + global config."""

from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import apt, git


@deploy("Configure git")
def deploy_git():
    apt.packages(name="Install git", packages=["git"], present=True)

    # git normalizes variable names to lowercase in its own storage, and the GitConfig
    # fact reads them back that way - mixed-case keys here would never match, so config
    # would be reapplied (falsely "changed") on every run.
    config = {
        "user.name": host.data.git_user_name,
        "user.email": host.data.git_user_email,
        "core.filemode": "true",
        "push.autosetupremote": "true",
        "init.defaultbranch": "main",
        "push.default": "current",
    }
    for key, value in config.items():
        git.config(
            name=f"Set git {key}",
            key=key,
            value=value,
            _sudo=False,
        )


deploy_git()
