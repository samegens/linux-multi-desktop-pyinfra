"""Shared gsettings/dconf helpers for Cinnamon settings modules (keyboard.py, lock_screen.py).
"""

import re

from pyinfra.context import host
from pyinfra.facts.server import Command

def get_list(schema: str, key: str) -> list[str]:
    # _sudo=False - gsettings reads the per-user dconf session; under the global SUDO=True
    # default this would read root's (empty) dconf instead and never see an already-set
    # option, re-running the write every deploy.
    output = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command, command=f"gsettings get {schema} {key}", _sudo=False
    )
    return re.findall(r"'([^']*)'", output) if output else []

def format_list(values: list[str]) -> str:
    # An empty `[]` literal is a type-less GVariant that `dconf write` refuses ("unable to
    # infer type") - `@as []` explicitly types it as an array of strings. Confirmed live
    # against dell_laptop.
    if not values:
        return "@as []"
    return "[" + ", ".join(f"'{value}'" for value in values) + "]"
