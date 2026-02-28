from __future__ import annotations

from pathlib import Path

from app.video.project_bundle import ensure_remotion_bundle


def test_ensure_remotion_bundle_writes_entry_files(tmp_path: Path) -> None:
    entry = ensure_remotion_bundle(tmp_path / "video")

    assert entry.exists()
    assert entry.name == "index.jsx"
    assert (entry.parent / "Root.jsx").exists()
    assert (entry.parent / "MainVideo.jsx").exists()
