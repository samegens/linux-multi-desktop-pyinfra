"""Gitleaks - pattern-based secret scanner, one of the three tools the pre-commit hook
(.githooks/check-secrets) runs before every commit. No apt/dnf packaging - a GitHub-release
.tar.gz containing a single binary, extracted straight onto /usr/local/bin.

Deliberately not version-pinned via group_data like this repo's other GitHub-release installs
(e.g. starship.py) - a secret scanner is only as good as its detection rules, so this always
tracks upstream's latest release rather than a version fixed at write time.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.facts.server import Arch

from archives import download_and_extract_latest_release

ARCH_MAP = {
    "x86_64": "x64",
    "aarch64": "arm64",
}

@deploy("Install Gitleaks")
def deploy_gitleaks():
    arch = ARCH_MAP[host.get_fact(Arch)] # pyright: ignore[reportUnknownMemberType]
    download_and_extract_latest_release(
        name="Download and extract the latest Gitleaks release",
        tag_api_url="https://api.github.com/repos/gitleaks/gitleaks/releases/latest",
        tarball_url_template=(
            "https://github.com/gitleaks/gitleaks/releases/download/"
            f"v{{version}}/gitleaks_{{version}}_linux_{arch}.tar.gz"
        ),
        dest="/usr/local/bin",
        version_check_command="gitleaks version",
    )

deploy_gitleaks()
