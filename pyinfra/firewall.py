"""Firewall trust-rule abstraction - firewalld on Fedora/dnf, ufw on Mint/apt (Fedora has no
ufw; Mint's remote VM has no firewalld at all - confirmed live, neither the binary nor the
service exists there). No dedicated pyinfra operation for either tool, so this shells out
directly with a check-first pattern, same as base.py's flatpak-remote handling. Only exposes
what modules/k3s.py needs today (trusting a CIDR source unconditionally) - not a general
firewall-rule DSL.
"""

from typing import assert_never

from pyinfra.context import host
from pyinfra.facts.server import Command
from pyinfra.operations import server

from pkgmgr import PackageManager, get_package_manager

def trust_source(name: str, source: str):
    """Allow all traffic from `source` (a CIDR) unconditionally - matches fedora-desktop's
    firewalld `zone: trusted` rule for k3s's pod/service networks."""
    pm = get_package_manager()
    match pm:
        case PackageManager.DNF:
            _trust_source_firewalld(name, source)
        case PackageManager.APT:
            _trust_source_ufw(name, source)
        case _:
            assert_never(pm)

def _trust_source_firewalld(name: str, source: str):
    already_trusted = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=f"firewall-cmd --zone=trusted --query-source={source} 2>/dev/null || true",
    )
    if already_trusted and already_trusted.strip() == "yes":
        host.noop(f"{source} already trusted in firewalld")
        return

    server.shell(
        name=name,
        commands=[
            f"firewall-cmd --zone=trusted --add-source={source} --permanent",
            "firewall-cmd --reload",
        ],
    )

def _trust_source_ufw(name: str, source: str):
    # `ufw status` only lists rules while ufw itself is active - confirmed live it prints
    # nothing but "Status: inactive" even with real rules persisted, which made this always
    # re-run `ufw allow` (harmless - ufw itself dedupes - but never showed as idempotent).
    # Check the persisted ruleset file directly instead, which reflects reality either way.
    existing = host.get_fact( # pyright: ignore[reportUnknownMemberType]
        Command,
        command=f"grep -qF -- '-s {source} -j ACCEPT' /etc/ufw/user.rules 2>/dev/null && echo yes || echo no",
    )
    if existing and existing.strip() == "yes":
        host.noop(f"{source} already trusted in ufw")
        return

    server.shell(name=name, commands=[f"ufw allow from {source}"])
