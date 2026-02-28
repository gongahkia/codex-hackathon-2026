# `LastMinute`

This repository is now the canonical source of truth for `last-minute`.

`LastMinute` is a Codex skill for solo hackathon builders. It supports:

1. intake from either a raw problem statement or a `Devpost`/`Luma` hackathon link,
2. research and ranked build options,
3. judging-rubric + prize-track alignment,
4. checkpoint-based scope replanning,
5. submission artifacts + judge Q&A pack,
6. automated Remotion demo generation (with fallback output if renderer is unavailable).

## Quickstart (Codex Skill)

1. Install the skill locally:

```bash
mkdir -p "$HOME/.codex/skills/last-minute/agents"
cp skills/last-minute/SKILL.md "$HOME/.codex/skills/last-minute/SKILL.md"
cp skills/last-minute/agents/openai.yaml "$HOME/.codex/skills/last-minute/agents/openai.yaml"
```

2. Restart Codex.

3. Open Skills in Codex and enable/search for `Last Minute`.

4. Invoke it in chat:

```text
Use $last-minute.
Hackathon URL: https://devpost.com/hackathons/<event>  (or a lu.ma link)
Deadline: 8 hours
Mode: detailed-live
Judging rubric: Innovation, technical quality, impact
Prize tracks: AI Track, Education Prize, Social Good
Deployment health URL: https://<your-app>/health
Demo route: /demo
```

You can also run with a direct problem statement instead of a URL.

## CLI Usage

Run with hackathon URL intake:

```bash
python -m app.cli run \
  --hackathon-url "https://devpost.com/hackathons/<event>" \
  --deadline-hours 8 \
  --mode detailed-live \
  --judging-rubric "Innovation, technical quality, impact" \
  --prize-tracks "AI Track, Education Prize, Social Good" \
  --deployment-health-url "https://<your-app>/health" \
  --demo-route "/demo"
```

Run with direct problem statement:

```bash
python -m app.cli run \
  --problem-statement "Build an AI classroom assistant" \
  --deadline-hours 8
```

## What It Produces

Run artifacts are written to:

```text
runs/<run_id>/artifacts/
```

Common outputs:

1. `intake-summary.json`
2. `research-summary.json`
3. `ranking-preview.json`
4. `selection.json`
5. `checkpoint-replan.json`
6. `submission.md`
7. `pitch-narrative.json` (`60/90/120` sec scripts)
8. `judge-qa.md`
9. `demo-reliability.json`
10. `deployment-health.json` (if URL provided)
11. `testing-report.json`
12. `remotion.config.json`
13. `video-result.json`

## Security Hardening (Enforced)

1. command allowlist is enforced before subprocess execution,
2. secret redaction is applied to command output serialization,
3. remote URL fetches are restricted to HTTPS and public IP destinations,
4. redirects across domain boundaries are blocked by default,
5. response content-type and byte limits are enforced on remote fetches,
6. artifact writes are constrained to resolved run-local roots (path traversal blocked).
