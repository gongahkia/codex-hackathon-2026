"""Secret redaction helpers."""

from __future__ import annotations

import re

SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(token\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(secret\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(authorization\s*:\s*bearer\s+)([^\s,;]+)", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Redact common secret-like key/value patterns from logs."""

    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r"\1***REDACTED***", redacted)
    return redacted
