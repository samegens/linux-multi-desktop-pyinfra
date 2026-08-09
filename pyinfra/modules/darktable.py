"""darktable - RAW photo editor, flatpak. Installs its own flatpak (base.py's Flathub remote
setup is a prerequisite - see modules/base.py) rather than going through
host.data.flatpaks, so the package and the handful of deliberate settings this module pins
in its config live together in one file. Settings were found by diffing a real darktablerc
against the flatpak's own shipped-default template - not by copying the whole file wholesale
(see keyfile.py's set_key_value operation for why).
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files, flatpak

from keyfile import set_key_value

# key -> value, exactly as darktablerc itself stores them (e.g. its own TRUE/FALSE spelling,
# not Python's True/False). Only settings confirmed to be deliberate choices - not session
# state (window size, last import folder, ...) or default-vs-live noise from darktable's own
# float/bool reformatting - belong here.
DARKTABLERC_SETTINGS: dict[str, str] = {
    "plugins/darkroom/workflow": "scene-referred (filmic)",
    "plugins/darkroom/histogram/mode": "histogram",
    "plugins/imageio/format/jpeg/quality": "85",
    "session/use_filename": "TRUE",
}

@deploy("Configure darktable")
def deploy_darktable():
    username = host.data.username
    config_dir = f"/home/{username}/.var/app/org.darktable.Darktable/config/darktable"
    darktablerc = f"{config_dir}/darktablerc"

    flatpak.packages(
        name="Install darktable",
        packages=["org.darktable.Darktable"],
        remote="flathub",
        present=True,
    )

    files.directory(
        name="Create darktable config directory",
        path=config_dir,
        user=username,
        group=username,
        mode="700",
        _sudo=False,
    )

    for key, value in DARKTABLERC_SETTINGS.items():
        set_key_value(
            name=f"Set darktable setting {key}={value}",
            path=darktablerc,
            key=key,
            value=value,
            _sudo=False,
        )

deploy_darktable()
