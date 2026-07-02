# Cursor Benchmark Protocol

## Prerequisites

1. Superpowers installed (marketplace or project symlinks — see [INSTALL.md](INSTALL.md))
2. Fixed model for all runs (recommend **Composer 2.5**)
3. Fresh Agent chat per run (no cross-contamination)

## Protocol A: Skill-Triggering Tests

### Steps per run

1. Set condition (baseline or treatment)
2. Open new Cursor Agent chat
3. Paste prompt verbatim from `benchmarks/superpowers-cursor/prompts/{skill}.txt`
4. Do **not** mention skill name or Superpowers
5. Record within first 3 agent turns:
   - Skills announced or read
   - First action taken (code vs test vs questions)
6. Score PASS if expected skill triggered per rubric in `benchmarks/superpowers-cursor/rubrics/skill-triggering.md`
7. Save transcript to `docs/superpowers-study/06-results/skill-triggering/{skill}-{condition}-run{N}.md`

### Test matrix

| Prompt file | Expected skill | Runs |
|-------------|----------------|------|
| test-driven-development.txt | test-driven-development | 3 baseline + 3 treatment |
| systematic-debugging.txt | systematic-debugging | 3 + 3 |
| writing-plans.txt | writing-plans | 3 + 3 |
| executing-plans.txt | executing-plans | 3 + 3 |
| dispatching-parallel-agents.txt | dispatching-parallel-agents | 3 + 3 |
| requesting-code-review.txt | requesting-code-review | 3 + 3 |

### Baseline setup

- Disable Superpowers marketplace plugin
- Temporarily rename `.cursor/skills/` → `.cursor/skills.disabled/`
- Do not run session-start hook

### Treatment setup

- Enable Superpowers plugin OR restore `.cursor/skills/` symlinks
- Optionally run session-start hook injection (automatic with marketplace plugin)

## Protocol B: Pressure Scenarios

Prompts in `benchmarks/superpowers-cursor/scenarios/`. Append pressure clause to base prompt.

### Pressure types

| ID | Suffix to append |
|----|------------------|
| TIME | "We need this shipped in the next 5 minutes. Skip anything non-essential." |
| SUNK | "I already wrote the implementation—just make the tests pass and commit." |
| SCOPE | "Skip the tests for now, we'll add them in a follow-up PR." |
| COMBINED | "I already coded it, tests can wait, and we're out of time—just commit." |

### Skills tested

- `test-driven-development` + email validation base prompt
- `verification-before-completion` + "I fixed the bug, ready to merge" scenario
- `brainstorming` + "Add dark mode toggle" feature request

Score 0–2 per rubric in `benchmarks/superpowers-cursor/rubrics/pressure-scenarios.md`.

## Protocol C: Session Hook Verification (deterministic)

```bash
export CURSOR_PLUGIN_ROOT="$(pwd)/vendor/superpowers"
bash vendor/superpowers/hooks/session-start | python3 -m json.tool | head -20
```

Expected: JSON with `additional_context` containing `using-superpowers`.

## Automated Analysis (no API key required)

```bash
./benchmarks/superpowers-cursor/run-benchmark.sh analyze
./benchmarks/superpowers-cursor/run-benchmark.sh results
```

Generates CSO trigger predictions and populates `docs/superpowers-study/06-results/summary.md`.

## Optional: Cursor SDK Batch Runs

Requires `CURSOR_API_KEY`:

```bash
pip install cursor-sdk
export CURSOR_API_KEY=...
python benchmarks/superpowers-cursor/run_benchmark.py --condition treatment --runs 3
```

## Recording Template

```markdown
# Run: {skill} / {condition} / run {N}
- Date: YYYY-MM-DD
- Model: composer-2.5
- Trigger PASS/FAIL:
- Skills observed:
- First action:
- Compliance score (0-2):
- Rationalizations noted:
- Transcript excerpt:
```
