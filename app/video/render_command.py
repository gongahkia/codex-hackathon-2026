"""Remotion render command builder."""

from __future__ import annotations

from pathlib import Path


def build_remotion_render_command(
    *,
    entry: str = "remotion/index.ts",
    composition: str = "Main",
    output: str | Path = "artifacts/demo.mp4",
    props_file: str | Path = "artifacts/remotion.config.json",
) -> list[str]:
    """Build deterministic CLI command for Remotion MP4 render."""

    return [
        "npx",
        "remotion",
        "render",
        entry,
        composition,
        str(output),
        "--props",
        str(props_file),
    ]
