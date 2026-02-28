# `LastMinute`

`LastMinute` is a Codex skill for solo hackathon builders with the following workflow.

1. Feed either a raw problem statement or a `Devpost`/`Luma` hackathon link
2. Research and ranked build options
3. Judging-rubric + prize-track alignment
4. Checkpoint-based scope replanning
5. Submission artifacts + Judge Q&A pack
6. Automated Remotion demo generation 

## Quickstart 

1. Install the skill locally.

```console
$ mkdir -p "$HOME/.codex/skills/last-minute/agents"
$ cp skills/last-minute/SKILL.md "$HOME/.codex/skills/last-minute/SKILL.md"
$ cp skills/last-minute/agents/openai.yaml "$HOME/.codex/skills/last-minute/agents/openai.yaml"
```

2. Restart Codex.

3. Open Skills in Codex and enable/search for `LastMinute`.

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