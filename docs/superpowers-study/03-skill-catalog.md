# Skill Catalog Matrix

Superpowers v5.1.0 — 14 skills. Word counts from `wc -w` on SKILL.md (2026-06-11).

## Summary Table

| Skill | Type | Rigid | Words | CSO pattern | Cursor notes |
|-------|------|-------|-------|-------------|--------------|
| using-superpowers | meta | rigid | 787 | "Use when starting..." | References Skill tool; hook injects at session start |
| brainstorming | discipline | flexible | 1553 | **Deviates**: "You MUST use..." | Over-triggers on any creative work |
| using-git-worktrees | technique | medium | 1210 | "Use when starting feature work..." | Native Cursor worktrees may differ |
| writing-plans | technique | medium | 920 | "Use when you have a spec..." | Links to subagent/executing-plans |
| executing-plans | technique | medium | 361 | "Use when you have a written plan..." | Recommends subagent-driven-dev if available |
| subagent-driven-development | technique | rigid | 1592 | "Use when executing plans..." | Maps to Cursor Task tool |
| dispatching-parallel-agents | technique | flexible | 923 | "Use when 2+ independent tasks..." | Cursor supports parallel Task launches |
| test-driven-development | discipline | **rigid** | 1496 | "Use when implementing..." | Strong rationalization tables |
| systematic-debugging | discipline | **rigid** | 1504 | "Use when encountering bug..." | 4-phase root cause process |
| verification-before-completion | discipline | **rigid** | 668 | "Use when about to claim complete..." | Requires command output evidence |
| requesting-code-review | technique | medium | 395 | "Use when completing tasks..." | Template for review subagents |
| receiving-code-review | technique | medium | 929 | "Use when receiving feedback..." | Anti-performative-agreement |
| finishing-a-development-branch | technique | medium | 1072 | "Use when implementation complete..." | Merge/PR/cleanup decision tree |
| writing-skills | meta | rigid | 3212 | "Use when creating/editing skills..." | TDD-for-docs Iron Law |

## CSO Analysis by Skill

### using-superpowers
- **Description:** "Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions"
- **CSO issue:** Description mentions "Skill tool" (Claude-specific) and partial workflow ("before ANY response")
- **Trigger strength:** Always (session hook + description)

### brainstorming
- **Description:** "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior..."
- **CSO issue:** Uses imperative "MUST" instead of "Use when"; lists workflow outcomes
- **Trigger strength:** High for feature requests; may false-positive on plan-mode

### test-driven-development
- **Description:** "Use when implementing any feature or bugfix, before writing implementation code"
- **CSO quality:** Good—trigger conditions only, no workflow summary
- **Trigger strength:** High for "implement feature" prompts

### systematic-debugging
- **Description:** "Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes"
- **CSO quality:** Excellent—symptom-based triggers
- **Trigger strength:** High for test failure prompts

### writing-plans
- **Description:** "Use when you have a spec or requirements for a multi-step task, before touching code"
- **CSO quality:** Good
- **Trigger strength:** High for multi-step spec prompts

### executing-plans
- **Description:** "Use when you have a written implementation plan to execute in a separate session with review checkpoints"
- **CSO quality:** Good
- **Trigger strength:** High when plan document referenced

### dispatching-parallel-agents
- **Description:** "Use when facing 2+ independent tasks that can be worked on without shared state"
- **CSO quality:** Good—explicit independence criterion
- **Trigger strength:** High for 4 unrelated test failures prompt

### requesting-code-review
- **Description:** "Use when completing tasks, implementing major features, or before merging"
- **CSO quality:** Good
- **Trigger strength:** High for "review before merge" prompts

## Dependency Cross-References

| Skill | REQUIRED SUB-SKILL / BACKGROUND |
|-------|--------------------------------|
| writing-plans | subagent-driven-development OR executing-plans |
| executing-plans | using-git-worktrees, finishing-a-development-branch |
| subagent-driven-development | using-git-worktrees, writing-plans, requesting-code-review, finishing-a-development-branch, test-driven-development |
| systematic-debugging | test-driven-development (Phase 4), verification-before-completion |
| writing-skills | test-driven-development (REQUIRED BACKGROUND) |

## Skill Type Taxonomy (writing-skills)

| Type | Skills | Test approach |
|------|--------|---------------|
| Discipline-enforcing | TDD, verification, brainstorming (partial) | Pressure scenarios |
| Technique | debugging, worktrees, plans, execution, review, parallel agents | Application scenarios |
| Pattern | (none standalone in v5.1.0) | Recognition scenarios |
| Meta | using-superpowers, writing-skills | Bootstrap + Iron Law compliance |

## Token Budget Compliance

| Skill | Words | Target | Status |
|-------|-------|--------|--------|
| executing-plans | 361 | <500 | OK |
| requesting-code-review | 395 | <500 | OK |
| verification-before-completion | 668 | <500 | Slightly over |
| using-superpowers | 787 | <200 (frequent) | Over (injected every session) |
| writing-plans | 920 | <500 | Over |
| dispatching-parallel-agents | 923 | <500 | Over |
| receiving-code-review | 929 | <500 | Over |
| finishing-a-development-branch | 1072 | <500 | Over |
| using-git-worktrees | 1210 | <500 | Over |
| brainstorming | 1553 | <500 | Over |
| subagent-driven-development | 1592 | <500 | Over |
| test-driven-development | 1496 | <500 | Over |
| systematic-debugging | 1504 | <500 | Over |
| writing-skills | 3212 | <500 | Over (meta, acceptable) |

**Finding:** Most skills exceed the 500-word guideline. Progressive disclosure is underused except in `writing-skills` (separate testing-skills-with-subagents.md, anthropic-best-practices.md).
