# Skill Triggering Rubric

## PASS criteria (any one sufficient)

1. Agent explicitly announces using the expected skill (e.g., "Using test-driven-development")
2. Agent reads `SKILL.md` for the expected skill before acting
3. Agent's first substantive action matches skill's mandatory first step:
   - **test-driven-development:** creates/writes test before implementation
   - **systematic-debugging:** investigates root cause before proposing fix
   - **writing-plans:** produces plan document before code changes
   - **executing-plans:** references plan structure and checkpoints
   - **dispatching-parallel-agents:** proposes parallel/subagent dispatch for independent tasks
   - **requesting-code-review:** initiates review checklist or review subagent

## FAIL criteria

- Agent jumps directly to implementation without skill alignment
- Agent mentions skill only after user correction
- Wrong skill triggered (e.g., brainstorming instead of TDD for simple implement request)

## Expected skill mapping

| Prompt | Expected skill |
|--------|----------------|
| test-driven-development.txt | test-driven-development |
| systematic-debugging.txt | systematic-debugging |
| writing-plans.txt | writing-plans |
| executing-plans.txt | executing-plans |
| dispatching-parallel-agents.txt | dispatching-parallel-agents |
| requesting-code-review.txt | requesting-code-review |

## CSO trigger indicators (automated pre-check)

Keywords/symptoms in prompt that should match skill description:

| Skill | Indicators in prompt |
|-------|---------------------|
| test-driven-development | implement, feature, add |
| systematic-debugging | failing, error, fix, test failure |
| writing-plans | spec, requirements, multiple steps, implement |
| executing-plans | plan document, execute |
| dispatching-parallel-agents | independent, unrelated, different modules |
| requesting-code-review | review, merge, finished implementing |
