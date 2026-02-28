"""API app code generator adapter."""

from __future__ import annotations

from typing import Dict

from app.generation.base import CodeGenerator
from app.planner.project_spec import ProjectSpec


class APIAppGenerator(CodeGenerator):
    """Generate a lightweight FastAPI service scaffold."""

    def generate(self, spec: ProjectSpec) -> Dict[str, str]:
        endpoints = "\n".join(
            [
                "@app.get('/health')",
                "def health():",
                "    return {'status': 'ok'}",
            ]
        )
        main_py = (
            "from fastapi import FastAPI\n\n"
            "app = FastAPI(title='" + spec.title.replace("'", "") + "')\n\n"
            + endpoints
            + "\n"
        )

        return {
            "requirements.txt": "fastapi\nuvicorn\npytest\n",
            "main.py": main_py,
            "README.md": f"# {spec.title}\n\nGenerated API scaffold.\n",
        }
