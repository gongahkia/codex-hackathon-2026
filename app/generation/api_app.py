"""API app code generator adapter."""

from __future__ import annotations

import json
from typing import Dict

from app.generation.base import CodeGenerator
from app.planner.project_spec import ProjectSpec


class APIAppGenerator(CodeGenerator):
    """Generate a deterministic Python API-logic scaffold with integration tests."""

    def generate(self, spec: ProjectSpec) -> Dict[str, str]:
        feature_seed = ", ".join(json.dumps(feature) for feature in spec.features)
        main_py = (
            "from __future__ import annotations\n\n"
            "from dataclasses import dataclass, field\n\n"
            "@dataclass\n"
            "class WorkItem:\n"
            "    name: str\n"
            "    complete: bool = False\n\n"
            "@dataclass\n"
            "class ProjectPlan:\n"
            "    title: str\n"
            "    items: list[WorkItem] = field(default_factory=list)\n\n"
            "    def mark_complete(self, index: int) -> None:\n"
            "        self.items[index].complete = True\n\n"
            "    def readiness(self) -> float:\n"
            "        if not self.items:\n"
            "            return 1.0\n"
            "        complete = sum(1 for item in self.items if item.complete)\n"
            "        return round(complete / len(self.items), 2)\n\n"
            "    def summary(self) -> str:\n"
            "        complete = sum(1 for item in self.items if item.complete)\n"
            "        return f\"{self.title}: {complete}/{len(self.items)} core features complete.\"\n\n"
            "def build_demo_plan() -> ProjectPlan:\n"
            f"    seeded = [{feature_seed}]\n"
            "    plan = ProjectPlan(title="
            + json.dumps(spec.title)
            + ", items=[WorkItem(name=item) for item in seeded])\n"
            "    if plan.items:\n"
            "        plan.mark_complete(0)\n"
            "    return plan\n\n"
            "if __name__ == '__main__':\n"
            "    plan = build_demo_plan()\n"
            "    print(plan.summary())\n"
        )

        integration_test = (
            "import pytest\n\n"
            "from main import build_demo_plan\n\n"
            "@pytest.mark.integration\n"
            "def test_plan_reaches_complete_state() -> None:\n"
            "    plan = build_demo_plan()\n"
            "    assert 0 <= plan.readiness() <= 1\n"
            "    for idx in range(len(plan.items)):\n"
            "        plan.mark_complete(idx)\n"
            "    assert plan.readiness() == 1.0\n"
            "    assert 'core features complete' in plan.summary()\n"
        )

        feature_list = "\n".join(f"- {feature}" for feature in spec.features)
        readme = (
            f"# {spec.title}\n\n"
            "Generated deterministic Python API-logic scaffold.\n\n"
            "## Core Features\n"
            f"{feature_list}\n\n"
            "## Commands\n"
            "- `pytest -m integration`\n"
            "- `python3 main.py`\n"
        )

        return {
            "main.py": main_py,
            "tests/test_integration.py": integration_test,
            "pytest.ini": "[pytest]\nmarkers =\n    integration: integration flow checks\n",
            "README.md": readme,
        }
