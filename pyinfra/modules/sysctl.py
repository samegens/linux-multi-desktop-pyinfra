"""/etc/sysctl.conf tweaks. Currently just raises inotify watch/instance limits, needed by
file-watching software (Dropbox, VS Code, Node dev servers) to avoid silently missing changes
once it hits the kernel's low defaults.
"""

from pyinfra.context import host
from pyinfra.api.deploy import deploy # pyright: ignore[reportUnknownVariableType]
from pyinfra.operations import files, server

SYSCTL_CONF = "/etc/sysctl.conf"

SYSCTL_SETTINGS: dict[str, str] = {
    "fs.inotify.max_user_watches": "524288",
    "fs.inotify.max_user_instances": "512",
}

@deploy("Configure sysctl")
def deploy_sysctl():
    changed = False

    for key, value in SYSCTL_SETTINGS.items():
        op = files.line(
            name=f"Set {key} in {SYSCTL_CONF}",
            path=SYSCTL_CONF,
            line=rf"^{key}=.*$",
            replace=f"{key}={value}",
            extended_regex=True,
        )
        changed = changed or op.changed

    if changed:
        server.shell(name="Reload sysctl settings", commands=["sysctl -p"])
    else:
        host.noop("sysctl settings already applied")

deploy_sysctl()
