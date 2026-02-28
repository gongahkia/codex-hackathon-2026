"""Web app code generator adapter."""

from __future__ import annotations

import json
from typing import Dict

from app.generation.base import CodeGenerator
from app.planner.project_spec import ProjectSpec


class WebAppGenerator(CodeGenerator):
    """Generate a deterministic Node-based web scaffold with core logic tests."""

    def generate(self, spec: ProjectSpec) -> Dict[str, str]:
        app_name = spec.title.lower().replace(" ", "-")
        package_json = {
            "name": app_name,
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "node server.js",
                "start": "node server.js",
                "test": "npm run test:integration",
                "test:integration": "node --test tests/integration.test.js",
            },
        }

        seeded_features = ",\n".join(f"    {json.dumps(feature)}" for feature in spec.features)
        core_logic = (
            "export function createProjectState(title, features) {\n"
            "  return {\n"
            "    title,\n"
            "    features: features.map((name, index) => ({ id: index + 1, name, done: false })),\n"
            "    createdAt: new Date().toISOString(),\n"
            "  };\n"
            "}\n\n"
            "export function completeFeature(state, featureId) {\n"
            "  state.features = state.features.map((feature) =>\n"
            "    feature.id === featureId ? { ...feature, done: true } : feature\n"
            "  );\n"
            "  return state;\n"
            "}\n\n"
            "export function readinessScore(state) {\n"
            "  if (!state.features.length) {\n"
            "    return 1;\n"
            "  }\n"
            "  const done = state.features.filter((feature) => feature.done).length;\n"
            "  return Number((done / state.features.length).toFixed(2));\n"
            "}\n\n"
            "export function toSubmissionSummary(state) {\n"
            "  const done = state.features.filter((feature) => feature.done).length;\n"
            "  return `${state.title}: ${done}/${state.features.length} core features complete.`;\n"
            "}\n"
        )

        server_js = (
            "import http from 'node:http';\n"
            "import {\n"
            "  completeFeature,\n"
            "  createProjectState,\n"
            "  readinessScore,\n"
            "  toSubmissionSummary,\n"
            "} from './src/core-logic.js';\n\n"
            f"const initialFeatures = [\n{seeded_features}\n];\n"
            f"const state = createProjectState({json.dumps(spec.title)}, initialFeatures);\n"
            "if (state.features.length > 0) {\n"
            "  completeFeature(state, state.features[0].id);\n"
            "}\n\n"
            "const server = http.createServer((req, res) => {\n"
            "  if (req.url === '/health') {\n"
            "    res.writeHead(200, { 'content-type': 'application/json' });\n"
            "    res.end(JSON.stringify({ status: 'ok', readiness: readinessScore(state) }));\n"
            "    return;\n"
            "  }\n\n"
            "  if (req.url === '/api/summary') {\n"
            "    res.writeHead(200, { 'content-type': 'application/json' });\n"
            "    res.end(JSON.stringify({ summary: toSubmissionSummary(state), state }));\n"
            "    return;\n"
            "  }\n\n"
            "  res.writeHead(404, { 'content-type': 'application/json' });\n"
            "  res.end(JSON.stringify({ error: 'not_found' }));\n"
            "});\n\n"
            "const port = Number(process.env.PORT || 3000);\n"
            "server.listen(port, () => {\n"
            "  console.log(`server_ready:${port}`);\n"
            "});\n"
        )

        integration_test = (
            "import assert from 'node:assert/strict';\n"
            "import test from 'node:test';\n"
            "import {\n"
            "  completeFeature,\n"
            "  createProjectState,\n"
            "  readinessScore,\n"
            "  toSubmissionSummary,\n"
            "} from '../src/core-logic.js';\n\n"
            "test('core project logic reaches demo readiness', () => {\n"
            f"  const state = createProjectState({json.dumps(spec.title)}, ['Core flow', 'Submission output']);\n"
            "  assert.equal(readinessScore(state), 0);\n"
            "  completeFeature(state, 1);\n"
            "  assert.equal(readinessScore(state), 0.5);\n"
            "  completeFeature(state, 2);\n"
            "  assert.equal(readinessScore(state), 1);\n"
            "  const summary = toSubmissionSummary(state);\n"
            f"  assert.equal(summary.includes({json.dumps(spec.title)}), true);\n"
            "});\n"
        )

        feature_list = "\n".join(f"- {feature}" for feature in spec.features)
        readme = (
            f"# {spec.title}\n\n"
            "Generated deterministic web scaffold with end-to-end core logic.\n\n"
            "## Core Features\n"
            f"{feature_list}\n\n"
            "## Commands\n"
            "- `npm install`\n"
            "- `npm run test:integration`\n"
            "- `npm run dev`\n"
        )

        return {
            "package.json": json.dumps(package_json, indent=2),
            "server.js": server_js,
            "src/core-logic.js": core_logic,
            "tests/integration.test.js": integration_test,
            "README.md": readme,
        }
