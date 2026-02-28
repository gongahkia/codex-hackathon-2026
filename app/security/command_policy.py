"""Sandbox command allowlist policy."""

from __future__ import annotations

from typing import Sequence

ALLOWED_PREFIXES = {
    ("npm", "install"),
    ("npm", "run", "dev"),
    ("npm", "run", "test"),
    ("npm", "run", "test:integration"),
    ("pytest",),
    ("python3", "-m", "pytest"),
    ("python3", "-m", "unittest"),
    ("npx", "playwright", "test"),
    ("npm", "exec", "--yes", "--package=@remotion/cli@4.0.429", "--", "remotion", "render"),
    ("vercel", "deploy"),
    ("render", "deploy"),
}


def is_allowed_command(command: Sequence[str]) -> bool:
    """Check whether command is allowed by sandbox policy."""

    command_tuple = tuple(command)
    return any(command_tuple[: len(prefix)] == prefix for prefix in ALLOWED_PREFIXES)


def enforce_allowed_command(command: Sequence[str]) -> None:
    """Raise when command violates allowlist policy."""

    if not is_allowed_command(command):
        raise PermissionError(f"Command not allowed by policy: {' '.join(command)}")
