# How to Verify `last-minute` Skill Locally and on Another Laptop

## 1) Local Verification (Your Machine)

1. Open a terminal in the repo root:
```bash
cd /Users/gongahkia/Desktop/coding/projects/last-minute
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install minimum dependencies used by this repo:
```bash
python -m pip install --upgrade pip
pip install pydantic typer pytest
```

4. Run automated tests:
```bash
pytest -q
```

5. Confirm expected result:
```text
18 passed
```

6. Run a CLI smoke test:
```bash
python -m app.cli run \
  --problem-statement "Build an AI-powered task game" \
  --deadline-hours 6 \
  --mode fast
```

7. Confirm CLI result:
```text
A JSON config is printed and command exits with code 0.
```

8. Verify Reddit gate behavior:
```bash
python -m app.cli run \
  --problem-statement "Test Reddit opt-in" \
  --deadline-hours 4 \
  --include-reddit
```

9. Confirm expected Reddit gate failure:
```text
Command exits non-zero and prints that explicit confirmation is required.
```

## 2) Skill Behavior Check in Codex (Local)

1. Open Codex in this repo.

2. In chat, reference this skill file and give a realistic request:
```text
Use /Users/gongahkia/Desktop/coding/projects/last-minute/SKILL.md.
Problem: Build a lightweight game leaderboard app in 8 hours.
Mode: detailed-live.
Option count: 5.
```

3. Verify output shape includes these sections in order:
```text
Recommendation Summary
Ranked Options Matrix
Chosen Solution Plan
Implementation Summary
Testing Report
Demo Video Output Summary
```

4. Verify default policy behavior:
```text
Default mode is detailed-live unless overridden.
Reddit is not included unless explicitly opted in with disclaimer.
```

## 3) Verification on Friend's Laptop

1. On your machine, push all code to remote:
```bash
git add .
git commit -m "Add instruction doc and finalized skill implementation"
git push
```

2. On your friend's laptop, clone the same repo:
```bash
git clone <your-repo-url>
cd last-minute
```

3. Repeat environment setup on friend's laptop:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install pydantic typer pytest
```

4. Run the same automated validation:
```bash
pytest -q
```

5. Run the same CLI smoke test:
```bash
python -m app.cli run \
  --problem-statement "Build an AI-powered task game" \
  --deadline-hours 6 \
  --mode fast
```

6. Run Reddit gate test:
```bash
python -m app.cli run \
  --problem-statement "Test Reddit opt-in" \
  --deadline-hours 4 \
  --include-reddit
```

7. Confirm parity criteria:
```text
Tests pass on both machines.
CLI behavior and exit codes match on both machines.
Skill output section order and policy behavior match on both machines.
```

## 4) If You Move This into a Different Repository (for example, a game repo)

1. Copy these files/folders into the target repo:
```text
SKILL.md
app/
tests/
```

2. Add/update `.gitignore` in target repo with:
```text
__pycache__/
*.py[cod]
.pytest_cache/
```

3. Re-run the same setup and verification steps from Sections 1 and 2.

4. If paths change, update any absolute path references when invoking the skill in Codex.
