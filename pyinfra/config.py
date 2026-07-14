"""pyinfra config.

Bare uppercase vars here do nothing - pyinfra's CLI discards config.py's locals after
exec'ing it. Must mutate the live config object via the `pyinfra.config` context proxy.
"""

from pyinfra import config

config.SUDO = True
