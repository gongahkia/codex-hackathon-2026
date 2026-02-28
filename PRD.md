# PRD: last-minute

## 1. Product Summary

`last-minute` is an all-in-one Codex skill for solo hackathon builders. It converts a rough problem statement into:

1. Ranked solution options backed by live research.
2. A near-complete implementation of the selected option.
3. Testing results constrained by a user-specified deadline.
4. A Remotion demo video with configurable style and duration.

## 2. Target User and Constraints

### Primary Persona

- Solo hacker.

### Runtime Constraint

- User specifies a hard deadline from `1 hour` to `24 hours`.
- System must optimize for completion before deadline, even if scope must be reduced.

## 3. Goals and Non-Goals

### Goals (v1)

1. Shortlist strong implementation paths quickly from high-signal sources.
2. Let user choose a path with transparent scoring.
3. Build a near-complete app for the chosen path.
4. Produce best-possible test coverage within remaining time.
5. Produce a demo video via Remotion.

### Non-Goals (v1)

1. Multi-user/team collaboration workflows.
2. Guaranteed production hardening beyond hackathon quality.
3. Exhaustive source crawling of every platform in every run.

## 4. User Inputs

Required:

1. Problem statement.
2. Time budget (`1h-24h`).

Optional:

1. Preferred stack.
2. Mode: `fast` or `detailed-live`.
3. Number of ranked options to return (default `5`).
4. Scoring weights (user-adjustable).
5. Reddit inclusion toggle (default `off` with noise disclaimer).
6. Demo style and duration.

## 5. Modes

### `detailed-live` (default)

- Broader live research and deeper comparison before implementation.

### `fast`

- Reduced research depth and smaller option set to start coding earlier.

## 6. Source Policy

### Required-by-default Sources

1. DoraHacks
2. Devpost
3. GitHub

### Additional Sources

- Other large, accessible hackathon and dev sources when reachable.

### Optional Sources

- Reddit only when user explicitly opts in after a noise disclaimer.

### Quality Heuristics

Down-rank:

1. Low-detail or spam-like posts.
2. Stale or unmaintained repositories.
3. Weak evidence claims.

License restriction: none (all license families permitted for idea sourcing).

## 7. End-to-End Flow

1. Intake and configuration parsing.
2. Research and candidate extraction.
3. Deduplication and normalization.
4. Multi-factor scoring and ranking.
5. User selection of preferred solution.
6. Near-complete implementation.
7. Time-aware testing strategy.
8. Remotion demo generation.

## 8. Scoring Model

User controls weights. Suggested defaults:

1. Relevance: `0.35`
2. Feasibility: `0.30`
3. Speed-to-build: `0.20`
4. Evidence quality: `0.15`

Rules:

1. Normalize user weights to sum to `1.0`.
2. Show per-option component scores and final score.
3. Require minimum evidence threshold before recommendation:
   - at least one code artifact reference,
   - at least one build/writeup reference,
   - at least two independent source types.

## 9. Implementation Strategy

### Definition of "Near-Complete"

1. Core user flow fully implemented.
2. Main edge cases handled for hackathon demo reliability.
3. README with setup/run/deploy steps.

### Stack Defaults

- Choose fastest-to-ship defaults based on prompt and constraints.
- Prefer one-click deploy paths where possible; fallback to localhost flow.

## 10. Testing Strategy

Priority order, bounded by remaining time:

1. E2E tests if feasible.
2. Integration tests.
3. Smoke tests.

Time governor behavior:

1. If deadline risk rises, reduce test breadth but keep at least smoke coverage.
2. Always return explicit "what was tested vs skipped" report.

## 11. Demo Video Strategy (Remotion)

User-selectable templates:

1. Pitch-style video (short).
2. Full walkthrough video (longer).

User-configurable duration and style settings with sensible defaults if omitted.

## 12. Output Contract

For every run, return:

1. Short summary of top recommendations.
2. Detailed comparison matrix for all ranked options.
3. Chosen option implementation summary.
4. Testing report with coverage level and skipped items.
5. Demo video artifacts and run instructions.

## 13. Success Metrics

1. Time-to-ranked-options within mode target.
2. Share of runs that complete implementation within deadline.
3. Share of runs with at least smoke tests passing.
4. Share of runs producing demo video artifact.
5. User acceptance rate of top-ranked recommendation.

## 14. Risks and Mitigations

1. Risk: noisy live sources.
   - Mitigation: source-quality weighting + optional Reddit opt-in.
2. Risk: deadline overruns.
   - Mitigation: strict time governor and automatic scope trimming.
3. Risk: brittle E2E setup.
   - Mitigation: fallback ladder to integration/smoke with transparent reporting.
