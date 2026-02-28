# last-minute

`last-minute` is a Codex skill for solo hackathon builders. It takes a rough problem statement and drives:

1. live research and ranked solution options,
2. user selection of the best path,
3. near-complete implementation,
4. time-bounded testing,
5. Remotion demo video generation.

## Files

1. `PRD.md`: finalized product requirements and scope.
2. `SKILL.md`: executable skill behavior and output contract.

## Core Defaults

1. Deadline: user-configurable from `1h` to `24h`.
2. Mode: `detailed-live` by default, `fast` optional.
3. Required research sources: DoraHacks, Devpost, GitHub.
4. Ranked options: default `5`, user-configurable.
5. Reddit: optional opt-in with noise disclaimer.
6. Testing order: E2E -> integration -> smoke (time-dependent fallback).
