"""Sandbox command allowlist policy."""

from __future__ import annotations

from typing import Sequence

ALLOWED_PREFIXES = {
    ("npm", "install"),
    ("npm", "run", "dev"),
    ("npm", "run", "test"),
    ("pytest",),
    ("npx", "playwright", "test"),
    ("npx", "remotion", "render"),
}


def is_allowed_command(command: Sequence[str]) -> bool:
    """Check whether command is allowed by sandbox policy."""

    command_tuple = tuple(command)
    return any(command_tuple[: len(prefix)] == prefix for prefix in ALLOWED_PREFIXES)


def enforce_allowed_command(command: Sequence[str]) -> None:
    """Raise when command violates allowlist policy."""

    if not is_allowed_command(command):
        raise PermissionError(f"Command not allowed by policy: {' '.join(command)}")
