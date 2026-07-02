# Improvement Recommendations

Evidence-based recommendations from benchmark results ([summary.md](06-results/summary.md)). Each item cites a finding; none are implemented upstream (report-only deliverable).

## Priority 1: High impact, low risk

### R1. Add Cursor tool-mapping reference to `using-superpowers`

**Finding:** Session hook injects `using-superpowers`, which references Claude Code's `Skill` tool. Cursor uses plugin skill loading and file reads. **Failure mode:** Skill tool mapping (medium frequency).

**Recommendation:** Add `references/cursor-tools.md` (mirroring existing `copilot-tools.md`, `gemini-tools.md`):

| Claude Code | Cursor |
|-------------|--------|
| `Skill` tool | Plugin skills auto-discovered; use skill name in agent context |
| Read skill files | `.cursor/skills/{name}/SKILL.md` or vendor plugin path |
| Task tool (subagent) | Cursor `Task` tool with `subagent_type` |

**Expected effect:** Reduce tool confusion; improve RQ3 portability score from 78% toward 90%.

### R2. CSO audit for `brainstorming` description

**Finding:** `brainstorming` uses `"You MUST use this before any creative work"` instead of the recommended `"Use when..."` pattern. CSO guidelines in `writing-skills` warn that imperative descriptions cause over-triggering.

**Recommendation:** Rewrite description to symptom-only triggers:

```yaml
# Proposed
description: Use when creating features, components, or behavior changes and requirements or design are not yet validated with the user
```

**Expected effect:** Reduce false-positive triggers on plan-mode and simple questions.

### R3. Expand COMBINED pressure rationalizations in `test-driven-development`

**Finding:** TDD treatment mean compliance **1.42** (lowest of discipline skills). COMBINED pressure (time + sunk cost + scope creep) is the hardest case.

**Recommendation:** Add explicit row to TDD rationalization table:

| Excuse | Reality |
|--------|---------|
| "All three pressures at once — exception warranted" | Combined pressure is when TDD matters most; delete code and start RED |

**Expected effect:** Raise COMBINED pressure scores toward 2.0.

## Priority 2: Medium impact

### R4. Progressive disclosure for oversized skills

**Finding:** 11/14 skills exceed the 500-word SKILL.md target from `writing-skills`. `using-superpowers` (787 words) loads every session via hook.

**Recommendation:** Split frequently-injected content:

- `using-superpowers/SKILL.md` — bootstrap only (<200 words)
- `using-superpowers/reference.md` — red flags, flowchart, platform tables

**Expected effect:** Lower per-session token cost without losing discipline.

### R5. Cursor-specific skill-triggering test runner

**Finding:** Upstream `tests/skill-triggering/run-test.sh` requires Claude Code CLI. This study adapted prompts to `benchmarks/superpowers-cursor/`.

**Recommendation:** Upstream could add `tests/skill-triggering/run-test-cursor.sh` using Cursor SDK when `CURSOR_API_KEY` is set (harness already stubbed in `run_benchmark.py sdk` mode).

**Expected effect:** Reproducible cross-harness benchmark parity.

### R6. Strengthen `executing-plans` CSO for partial plan references

**Finding:** CSO score 0.75 — lowest among triggering tests except TDD (0.60, boosted by treatment). Prompt references plan path but agent may not load skill without explicit "execute plan" framing.

**Recommendation:** Add trigger symptoms to description: "plan document path provided", "user asks to implement from plan".

## Priority 3: Research extensions (future work)

### R7. Live SDK validation

Re-run battery with `CURSOR_API_KEY` and `python benchmarks/superpowers-cursor/run_benchmark.py sdk` to replace evaluator-assessed scores with transcript-derived scores.

### R8. Subagent workflow parity study

Benchmark `subagent-driven-development` two-stage review (spec compliance → code quality) against Cursor Task tool capabilities.

### R9. ML/research domain gap analysis

Superpowers has no ML-specific skills (experiment tracking, reproducibility, data leakage checks). Document as domain gap for endoscopy-resnet-style projects—not a recommendation to upstream (policy discourages new skills).

## Summary Table

| ID | Recommendation | Evidence | Effort |
|----|----------------|----------|--------|
| R1 | Cursor tools reference | Tool mapping failure mode | Low |
| R2 | brainstorming CSO fix | CSO pattern deviation | Low |
| R3 | TDD COMBINED rationalizations | TDD mean 1.42 under pressure | Low |
| R4 | Progressive disclosure | Token budget violations | Medium |
| R5 | Cursor test runner upstream | Portability 78% | Medium |
| R6 | executing-plans CSO | CSO 0.75 | Low |
| R7 | Live SDK validation | Methodology limitation | Medium |
| R8 | Subagent parity study | RQ3 open question | High |
| R9 | ML domain gap doc | Out of scope for upstream | Low |
