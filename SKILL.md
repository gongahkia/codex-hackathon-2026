---
name: last-minute
description: End-to-end hackathon build acceleration from rough problem statement to researched solution shortlist, ranked recommendation, near-complete implementation, time-bounded testing, and Remotion demo video. Use when a user needs to ship fast under a strict deadline (1-24 hours), compare build options from hackathon/dev sources, choose a path, and generate a working demo quickly.
---

# last-minute

Execute this skill to turn a hackathon problem statement into a shippable project under strict time limits.

## Operating Rules

1. Respect the user deadline as a hard cap (`1h-24h`).
2. Optimize for shipping a reliable demo, not maximal feature breadth.
3. Default to live research in `detailed-live` mode.
4. Offer `fast` mode to reduce research depth and begin implementation earlier.
5. Keep Reddit disabled by default and require explicit opt-in with a noise disclaimer.
6. Prefer one-click deploy targets when feasible; fallback to localhost instructions.

## Inputs

Collect and confirm:

1. Problem statement.
2. Deadline in hours (`1-24`).
3. Mode (`detailed-live` default, `fast` optional).
4. Ranked options count (default `5`).
5. Scoring weights (default: relevance `0.35`, feasibility `0.30`, speed `0.20`, evidence `0.15`).
6. Stack preference (optional).
7. Reddit inclusion (explicit opt-in only).
8. Remotion output preference:
   - `pitch` style,
   - `walkthrough` style,
   - custom duration.

Normalize scoring weights to sum to `1.0`.

## Required Research Sources

Use these by default:

1. DoraHacks
2. Devpost
3. GitHub

Add other large accessible hackathon/dev sources when useful.

## Workflow

### 1. Intake and Time Budgeting

1. Parse user inputs.
2. Split total time budget across phases:
   - research + ranking,
   - implementation,
   - testing,
   - demo generation.
3. Keep implementation + testing + demo time reserved before starting deep research.

### 2. Research and Candidate Extraction

1. Gather candidate approaches from required sources.
2. Extract:
   - project pattern,
   - stack,
   - complexity,
   - implementation evidence,
   - links.
3. Deduplicate near-identical ideas.

### 3. Quality Filtering

Down-rank candidates with:

1. weak implementation evidence,
2. stale repositories,
3. low-detail or spam-like writeups.

Allow all license families for inspiration and reference.

### 4. Scoring and Ranking

Score each candidate on:

1. relevance,
2. feasibility,
3. speed-to-build,
4. evidence quality.

Return:

1. short recommendation summary,
2. detailed matrix with factor scores and links,
3. top N options (default `5`).

### 5. User Selection Gate

Require explicit user selection of one ranked option before implementation.

### 6. Implementation

Build a near-complete app focused on demo readiness:

1. core flow complete,
2. essential error paths covered,
3. clear setup/run instructions,
4. deploy path if available.

Apply automatic scope trimming when deadline risk increases.

### 7. Testing

Follow this order based on remaining time:

1. E2E,
2. integration,
3. smoke.

If E2E is not feasible, fallback without blocking delivery. Always report what was run and skipped.

### 8. Demo Video (Remotion)

Generate the requested demo style:

1. pitch,
2. walkthrough.

Use sensible defaults when user does not specify duration or structure.

## Output Format

Return outputs in this order:

1. **Recommendation Summary**
2. **Ranked Options Matrix**
3. **Chosen Solution Plan**
4. **Implementation Summary**
5. **Testing Report**
6. **Demo Video Output Summary**

## Guardrails

1. Never promise full feature completeness when deadline does not allow it.
2. Prefer shipping a complete core flow over partial broad scope.
3. Keep all decisions traceable to deadline and scoring inputs.
4. Surface uncertainty explicitly when source quality is weak.
