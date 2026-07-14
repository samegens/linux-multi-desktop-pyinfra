"""Entrypoint. Calls each module's deploy() in order.

To run a subset, target a module file directly instead:
    pyinfra inventory.py modules/git.py --limit localhost
"""

from modules.base import deploy_base
from modules.bashrc import deploy_bashrc
from modules.git import deploy_git
from modules.ssh import deploy_ssh
from modules.starship import deploy_starship

deploy_base()
deploy_git()
deploy_ssh()
deploy_bashrc()
deploy_starship()
