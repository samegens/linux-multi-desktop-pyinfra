"""Python virtualenvs under ~/python3-venv, keyed by name -> pip packages. Ports the mechanism
from fedora-desktop's ansible/tasks/python-venv.yml (root dir + per-venv `python3 -m venv` +
pip-install a package list) - all four venvs that task manages, not just the one this repo
depends on, since this module is now the general replacement for that part of fedora-desktop's
Ansible.

pyinfra-latest is the venv this repo's own deploy runs from - prepare.sh bootstraps it manually
on a fresh box (chicken-and-egg: pyinfra isn't available to manage it before it exists), and
this module takes over keeping it present/up to date on every run after that. The other three
(ansible-latest, blauwe-lucht-rpa, ansible-homedisplay) are unrelated tools/projects with no
other connection to this repo - ported here only because this is where their venv management
mechanism now lives.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files, pip

import pkgmgr

VENVS: dict[str, list[str]] = {
    "pyinfra-latest": ["pyinfra", "privy"],
    "ansible-latest": ["ansible", "ansible-lint", "librouteros", "detect-secrets", "passlib"],
    "blauwe-lucht-rpa": ["rpa", "gspread", "oauth2client", "reportlab", "pypdf"],
    # Since homedisplay is running an old Raspbian, it needs an old version of Ansible.
    "ansible-homedisplay": ["ansible==9.13.0", "passlib"],
}

@deploy("Python virtualenvs")
def deploy_python_venv():
    username = host.data.username
    pkgmgr.install_venv_prerequisites(name="Install Python venv prerequisites")

    files.directory(
        name="Create ~/python3-venv",
        path=f"/home/{username}/python3-venv",
        user=username,
        group=username,
        mode="755",
        _sudo_user=username,
    )

    for venv_name, packages in VENVS.items():
        pip.packages( # pyright: ignore[reportUnknownMemberType]
            name=f"Install {venv_name} venv packages",
            packages=packages,
            virtualenv=f"/home/{username}/python3-venv/{venv_name}",
            virtualenv_kwargs={"venv": True, "python": "python3"},
            _sudo_user=username,
        )

deploy_python_venv()
