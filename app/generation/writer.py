"""Generated project filesystem writer."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping


def write_generated_project(
    run_id: str,
    files: Mapping[str, str],
    base_dir: str = "runs",
) -> Path:
    """Materialize generated files under runs/<run_id>/project."""

    root = Path(base_dir) / run_id / "project"
    root.mkdir(parents=True, exist_ok=True)

    for relative_path, content in files.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return root
