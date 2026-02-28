"""Deployment target resolution."""

from __future__ import annotations

from typing import Sequence


def resolve_deploy_target(stack: Sequence[str]) -> str:
    """Prefer Vercel for frontend-heavy stacks, else Render."""

    joined = " ".join(stack).lower()
    if any(token in joined for token in ("next", "react", "vite", "svelte", "nuxt")):
        return "vercel"
    return "render"


def resolve_deploy_plan(stack: Sequence[str], one_click_available: bool = True) -> dict[str, str]:
    """Return one-click deploy plan, fallback to localhost when unavailable."""

    if one_click_available:
        target = resolve_deploy_target(stack)
        return {
            "target": target,
            "command": "deploy --provider " + target,
        }

    return {
        "target": "localhost",
        "command": "npm install && npm run dev",
    }
