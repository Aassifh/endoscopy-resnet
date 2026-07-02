# Background and Related Work

## 1. Agent-Assisted Software Engineering

Coding agents (Claude Code, Cursor Agent, Codex, Copilot CLI) generate code from natural language. Without structured process, agents tend to:

- Jump directly to implementation
- Skip tests or write tests after code
- Claim success without verification
- Lose context on multi-step tasks

**Superpowers** (Jesse Vincent, Prime Radiant, Oct 2025) addresses this by packaging proven engineering practices as **composable skills**—markdown instruction files that agents must consult before acting.

## 2. Related Frameworks and Concepts

| Framework / Concept | Relationship to Superpowers |
|---------------------|----------------------------|
| **Agent Skills spec** ([agentskills.io](https://agentskills.io/specification)) | Formal metadata (`name`, `description`); Superpowers follows this |
| **SWE-bench / SWE-agent** | Task-completion benchmarks; Superpowers focuses on *process* compliance, not repo issue resolution |
| **Devin / autonomous agents** | End-to-end autonomy; Superpowers emphasizes human-in-loop design approval |
| **Cursor Rules / AGENTS.md** | Project-specific instructions; Superpowers skills are cross-project workflows |
| **TDD (Beck)** | Core philosophy; `test-driven-development` skill enforces RED-GREEN-REFACTOR |
| **Prompt engineering CSO** | Superpowers' "Claude Search Optimization"—descriptions trigger skill loading |

## 3. Superpowers Positioning

Superpowers is **not** a model or IDE. It is:

1. A **skills library** (14 skills in v5.1.0)
2. A **methodology** (brainstorm → design → plan → execute → review)
3. A **multi-harness plugin** (Claude Code, Cursor, Codex, Gemini, OpenCode, Copilot CLI)

Philosophy (from upstream README):

- Test-Driven Development — write tests first, always
- Systematic over ad-hoc — process over guessing
- Complexity reduction — simplicity as primary goal
- Evidence over claims — verify before declaring success

## 4. Why Study Superpowers on Cursor?

Cursor is a widely used agent harness with:

- Plugin marketplace (`/add-plugin superpowers`)
- Project skills (`.cursor/skills/`)
- Subagent Task tool (partial parity with Claude Code)
- Different skill-loading mechanics (no native `Skill` tool)

This study measures **how much of the upstream test battery transfers** and where Cursor-specific adaptations are needed.

## 5. Scope of This Study

**In scope:**

- Framework architecture review
- 14-skill catalog with CSO analysis
- Adapted skill-triggering tests (6 prompts × 2 conditions × 3 runs)
- Pressure scenarios (3 discipline skills × 4 pressure types × 3 runs)
- Evidence-based improvement recommendations

**Out of scope:**

- End-to-end ML tasks on endoscopy-resnet
- Upstream PRs to obra/superpowers
- New skill authoring (upstream policy discourages)

## 6. Primary Sources

| Source | Path / URL |
|--------|------------|
| Upstream repo (v5.1.0) | `vendor/superpowers/` |
| Release notes | `vendor/superpowers/RELEASE-NOTES.md` |
| Blog announcement | https://blog.fsck.com/2025/10/09/superpowers/ |
| Agent Skills spec | https://agentskills.io/specification |
| Upstream tests | `vendor/superpowers/tests/skill-triggering/` |
