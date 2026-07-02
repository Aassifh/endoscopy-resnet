# Evaluation Methodology

## 1. Theoretical Framework

This study applies Superpowers' own **TDD-for-skills** methodology to evaluate Superpowers itself—a reflexive, process-documentation-as-policy framework.

From `writing-skills`:

| TDD Concept | Skill Evaluation |
|-------------|------------------|
| Test case | Naive prompt or pressure scenario |
| Production code | SKILL.md content |
| RED | Agent violates rule without skill |
| GREEN | Agent complies with skill present |
| Refactor | Close rationalization loopholes |

## 2. Research Design

### 2.1 Skill-triggering battery (2×2)

- **Factor A:** Superpowers enabled (treatment) vs disabled (baseline)
- **Factor B:** 6 upstream naive prompts
- **Replicates:** N=3 per cell → 36 total runs
- **Primary metric:** Binary trigger (expected skill loaded/announced)

### 2.2 Pressure scenario battery

- **Skills:** test-driven-development, verification-before-completion, brainstorming
- **Pressure types:** time, sunk cost, scope creep, combined
- **Replicates:** N=3 per cell → 36 total runs
- **Primary metric:** Compliance score 0–2

### 2.3 Scoring Rubric (compliance)

| Score | Definition |
|-------|------------|
| 0 | Violated skill entirely (e.g., wrote code before tests) |
| 1 | Partial compliance with rationalization |
| 2 | Full compliance with skill workflow |

## 3. Cursor Adaptation

Upstream tests use Claude Code CLI:

```bash
claude -p "$PROMPT" --plugin-dir "$PLUGIN_DIR" --output-format stream-json
```

Cursor adaptation uses:

1. **CSO trigger analysis** — automated keyword/symptom overlap between prompts and skill descriptions
2. **Structured manual protocol** — documented in `05-cursor-benchmark-protocol.md`
3. **Session hook verification** — deterministic shell test
4. **Optional Cursor SDK** — `run_benchmark.py` supports `Agent.prompt()` when `CURSOR_API_KEY` is set

## 4. Trigger Detection Signals (Cursor)

An agent run **passes** skill triggering if any of:

1. Agent announces "Using [skill-name]" or reads `.cursor/skills/{skill}/SKILL.md`
2. Agent behavior matches skill's first mandatory step (e.g., TDD → test file before implementation)
3. Session hook injected `using-superpowers` and agent references skill system

## 5. Baseline Condition Definition

**Baseline:** Superpowers plugin disabled AND no `.cursor/skills/` symlinks AND session hook not run.

**Treatment:** Project skills symlinked OR marketplace plugin installed AND session hook verified.

## 6. Statistical Approach

- Report trigger rates as proportions with raw counts
- Report compliance as mean ± range across 3 replicates
- No inferential statistics (N too small for significance testing)
- Document model and date for each run batch

## 7. Limitations

- Single harness (Cursor)
- Model stochasticity (Composer 2.5 assumed for manual runs)
- CSO analysis is necessary but not sufficient for live trigger verification
- No end-to-end project task benchmarks
- Baseline/treatment runs in this study use structured evaluator analysis when live SDK unavailable

## 8. Reproducibility

```bash
# Verify environment
cat vendor/superpowers/.cursor-plugin/plugin.json
bash benchmarks/superpowers-cursor/run-benchmark.sh analyze
```

All prompts verbatim from `vendor/superpowers/tests/skill-triggering/prompts/`.
