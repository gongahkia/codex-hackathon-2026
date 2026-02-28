# `LastMinute`

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
2. `ranking-preview.json`
3. `checkpoint-replan.json`
4. `submission.md`
5. `pitch-narrative.json` (`60/90/120` sec scripts)
6. `judge-qa.md`
7. `demo-reliability.json`
8. `deployment-health.json` (if URL provided)
9. `remotion.config.json`
10. `video-result.json`
