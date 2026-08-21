"""GitHub-releases helper shared by any module that always wants the latest release rather than
a pinned version (see modules/k3s.py's docstring for why that's a deliberate per-module choice,
not the default convention elsewhere in this repo)."""

from pyinfra.context import host
from pyinfra.facts.server import Command

def latest_release_tag(repo: str) -> str:
    result = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=(
            f"curl -s https://api.github.com/repos/{repo}/releases/latest "
            "| python3 -c \"import json,sys; print(json.load(sys.stdin)['tag_name'])\""
        ),
    )
    return result.strip() if result else ""
