"""FreeCAD - parametric CAD, flatpak. Installs its own flatpak (base.py's Flathub remote setup
is a prerequisite - see modules/base.py) rather than going through host.data.flatpaks, so the
package and the handful of deliberate settings this module pins in its config live together in
one file, same as darktable.py. Settings were found by inspecting a real user.cfg: ~99% of it is
FreeCAD-generated window/color/session state (theme colors, dialog geometry, recent-files MRU,
sketch-value undo history) - no custom macros, saved preference packs, or materials existed to
port either. Only these 3 lines read as genuine deliberate choices rather than generated
defaults. Everything else (any custom macros/preference packs/materials, should the user ever
add some) is user data, not config drift - belongs in migrate.sh, not here.

user.cfg ships no default template inside the flatpak - FreeCAD only writes it at first run - so
this module reads back whatever's currently there (empty string if nothing yet), asks
xmlfile.set_element_text to fold in the desired settings (creating any missing FCParamGroup
nesting, even the document root itself, along the way), and writes the result back via
files.put - which already gives idempotent, diffable writes for free, same as every other
checked-in config file this repo manages, so this module needs no custom pyinfra operation of
its own. Verified live against a real FreeCAD GUI session on mint_vm: leaves pre-seeded this way
survive FreeCAD's own first-run merge of its usual window/session state into the same file.
"""

from io import StringIO

from pyinfra.context import host
from pyinfra.facts.server import Command
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files, flatpak

from xmlfile import Attribute, Element, set_element_text

_PREFERENCES_GENERAL = [
    Element("FCParameters"),
    Element("FCParamGroup", [Attribute("Name", "Root")]),
    Element("FCParamGroup", [Attribute("Name", "BaseApp")]),
    Element("FCParamGroup", [Attribute("Name", "Preferences")]),
    Element("FCParamGroup", [Attribute("Name", "General")]),
]
_PREFERENCES_VIEW = [
    Element("FCParameters"),
    Element("FCParamGroup", [Attribute("Name", "Root")]),
    Element("FCParamGroup", [Attribute("Name", "BaseApp")]),
    Element("FCParamGroup", [Attribute("Name", "Preferences")]),
    Element("FCParamGroup", [Attribute("Name", "View")]),
]

# (elements leading to the leaf's parent group, leaf name, value) - exactly as user.cfg itself
# stores them.
FCPARAM_SETTINGS: list[tuple[list[Element], str, str]] = [
    (_PREFERENCES_GENERAL, "AutoloadModule", "PartDesignWorkbench"),
    (_PREFERENCES_GENERAL, "FileExportFilter", "3D Manufacturing Format (*.3mf)"),
    (_PREFERENCES_VIEW, "NavigationStyle", "Gui::OpenSCADNavigationStyle"),
]

@deploy("Configure FreeCAD")
def deploy_freecad():
    username = host.data.username
    config_dir = f"/home/{username}/.var/app/org.freecad.FreeCAD/config/FreeCAD"
    user_cfg = f"{config_dir}/user.cfg"

    flatpak.packages(
        name="Install FreeCAD",
        packages=["org.freecad.FreeCAD"],
        remote="flathub",
        present=True,
    )

    files.directory(
        name="Create FreeCAD config directory",
        path=config_dir,
        user=username,
        group=username,
        mode="700",
        _sudo=False,
    )

    content = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=f"cat {user_cfg} 2>/dev/null || true",
        _sudo=False,
    ) or ""

    for group, param_name, value in FCPARAM_SETTINGS:
        content = set_element_text(content, [*group, Element("FCText", [Attribute("Name", param_name)])], value)

    files.put(
        name="Write FreeCAD settings",
        src=StringIO(content),
        dest=user_cfg,
        user=username,
        group=username,
        mode="644",
        _sudo=False,
    )

deploy_freecad()
