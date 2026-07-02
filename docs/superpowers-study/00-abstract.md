# Abstract: Superpowers Framework Review and Cursor Benchmark Study

## Summary

This study provides a systematic review of **Superpowers** (obra/superpowers v5.1.0)—an agentic skills framework and software development methodology—and evaluates its portability to **Cursor** using adapted versions of the upstream skill-triggering and pressure-scenario test batteries.

## Research Questions

| ID | Question | Finding (summary) |
|----|----------|-------------------|
| RQ1 | How does Superpowers enforce workflow discipline? | Mandatory skill chain + session hook injection of `using-superpowers`; discipline skills use rationalization tables and red-flag lists |
| RQ2 | Skill taxonomy, dependencies, CSO? | 14 skills in flat namespace; 4 types; CSO descriptions must avoid workflow summaries |
| RQ3 | Cursor portability? | **78%** portability score; hook verified; 6/6 upstream prompts adapted; Skill-tool references need Cursor mapping |
| RQ4 | Failure modes under pressure? | TDD weakest under COMBINED pressure (mean 1.42 treatment); baseline collapses to 0.17 mean compliance |
| RQ5 | Evidence-based improvements? | Cursor tool-mapping doc, CSO audit for `brainstorming`, expanded COMBINED pressure rationalizations |

## Method

- Literature-style analysis of upstream sources (README, 14 SKILL.md files, writing-skills methodology)
- Vendored upstream at `vendor/superpowers` (v5.1.0)
- Cursor benchmark harness in `benchmarks/superpowers-cursor/`
- CSO trigger analysis + structured evaluator assessment (N=3 per condition)
- Session-start hook verification via `CURSOR_PLUGIN_ROOT`

## Key Findings

1. Superpowers treats process documentation as **executable policy**, evaluated by its own TDD-for-skills Iron Law.
2. The workflow is a **directed graph** from brainstorming → worktree → plan → execution → TDD → review → finish.
3. Cursor session hook correctly injects `using-superpowers` via `additional_context` JSON (**PASS**).
4. **Treatment trigger rate:** 100% (18/18) vs **baseline:** 44% (8/18) — hook + skills bridge sub-threshold CSO prompts (e.g., TDD at 0.60).
5. **Pressure compliance:** treatment mean **1.64/2.0** vs baseline **0.17/2.0** — largest measurable benefit of the framework.

## Deliverable Location

Full report: `docs/superpowers-study/`  
Benchmark artifacts: `benchmarks/superpowers-cursor/`  
Upstream reference: `vendor/superpowers/`
