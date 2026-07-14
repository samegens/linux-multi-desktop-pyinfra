"""
Type stub for privy.core - upstream ships none. Signatures verified against the
installed package's source (privy 6.0.0).
"""

HASH_LENGTH: int
SALT_LENGTH: int
THREADS: int
MB: int
SECURITY_LEVELS: dict[int, dict[str, int]]

def hide(
    secret: bytes,
    password: str | bytes,
    security: int = ...,
    salt: bytes | None = ...,
    server: bool = ...,
) -> str: ...
def peek(
    hidden: str | bytes,
    password: str | bytes,
    expires: float | None = ...,
) -> bytes: ...

