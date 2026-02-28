"""Deployment target resolution."""

from __future__ import annotations

from typing import Sequence


def resolve_deploy_target(stack: Sequence[str]) -> str:
    """Prefer Vercel for frontend-heavy stacks, else Render."""

    joined = " ".join(stack).lower()
    if any(token in joined for token in ("next", "react", "vite", "svelte", "nuxt")):
        return "vercel"
    return "render"
