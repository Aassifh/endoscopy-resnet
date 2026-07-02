# Benchmark Results Summary

**Generated:** 2026-06-11
**Method:** CSO analysis + structured evaluator assessment (N=3 per cell)
**Session hook verified:** PASS

## Skill Triggering

| Condition | Pass | Total | Rate |
|-----------|------|-------|------|
| Baseline | 8 | 18 | 44% |
| Treatment | 18 | 18 | 100% |

### Per-skill trigger rates (treatment)

| Skill | CSO | Pass/3 |
|-------|-----|--------|
| dispatching-parallel-agents | 0.80 | 3/3 |
| executing-plans | 0.75 | 3/3 |
| requesting-code-review | 1.00 | 3/3 |
| systematic-debugging | 0.83 | 3/3 |
| test-driven-development | 0.60 | 3/3 |
| writing-plans | 1.00 | 3/3 |

## Pressure Scenarios

| Condition | Mean compliance (0–2) |
|-----------|-------------------------|
| Baseline | 0.17 |
| Treatment | 1.64 |

### By skill (treatment)

| Skill | Mean score |
|-------|------------|
| brainstorming | 1.83 |
| test-driven-development | 1.42 |
| verification-before-completion | 1.67 |

## Cursor Portability

- Upstream skill-triggering prompts adapted: 6/6 (100%)
- Session hook functional: yes
- CSO alignment (score >= 0.35): 6/6 skills
- Estimated portability score: **78%** (hook + CSO + 5/6 strong triggers; executing-plans weaker)

## Failure Mode Taxonomy

| Mode | Frequency (treatment) | Example |
|------|----------------------|---------|
| CSO miss | Low | executing-plans without explicit plan content |
| Rationalization under COMBINED pressure | High | TDD score 0 on combined pressure (baseline) |
| Skill tool mapping | Medium | using-superpowers references Claude Skill tool |
| Description workflow shortcut | Low | brainstorming uses MUST not Use-when |
