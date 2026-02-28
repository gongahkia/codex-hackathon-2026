"""Remotion scene config composer."""

from __future__ import annotations

import json
from typing import Iterable

from app.models.video import SceneSpec


def compose_remotion_config(scenes: Iterable[SceneSpec], fps: int = 30) -> str:
    """Emit Remotion scene configuration as JSON."""

    payload = {
        "fps": fps,
        "scenes": [scene.model_dump() for scene in scenes],
    }
    return json.dumps(payload, indent=2)
