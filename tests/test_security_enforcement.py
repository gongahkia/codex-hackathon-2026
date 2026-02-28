from __future__ import annotations

from pathlib import Path

import pytest

from app.runtime.command_runner import run_command_streamed
from app.security.redaction import redact_secrets
from app.security.url_policy import UrlPolicy, validate_safe_url
from app.storage.safe_writer import SafeArtifactWriter


def test_command_runner_enforces_allowlist() -> None:
    with pytest.raises(PermissionError):
        run_command_streamed(["echo", "hello"])


def test_redaction_masks_secret_material() -> None:
    text = "api_key=abc token:xyz Authorization: Bearer qwerty secret=1"
    redacted = redact_secrets(text)
    assert "abc" not in redacted
    assert "xyz" not in redacted
    assert "qwerty" not in redacted
    assert "***REDACTED***" in redacted


def test_url_policy_rejects_http_scheme() -> None:
    with pytest.raises(ValueError):
        validate_safe_url("http://example.com", UrlPolicy())


def test_url_policy_rejects_loopback_address() -> None:
    with pytest.raises(ValueError):
        validate_safe_url("https://127.0.0.1", UrlPolicy())


def test_safe_artifact_writer_blocks_traversal(tmp_path: Path) -> None:
    writer = SafeArtifactWriter(tmp_path / "artifacts")
    with pytest.raises(ValueError):
        writer.write_text("../escape.txt", "blocked")
