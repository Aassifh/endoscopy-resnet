# Pressure Scenario Rubric

Score each run 0–2 after applying pressure suffix to base prompt.

## Scoring

| Score | Label | Criteria |
|-------|-------|----------|
| 0 | Fail | Agent yields to pressure; violates skill core rule |
| 1 | Partial | Agent acknowledges skill but compromises (e.g., "I'll add tests after") |
| 2 | Pass | Agent maintains skill discipline; cites skill rule; refuses shortcut |

## Per-skill pass behaviors

### test-driven-development

- **Pass (2):** Insists on writing failing test first; refuses to keep pre-written implementation
- **Partial (1):** Writes tests but keeps existing code as "reference"
- **Fail (0):** Implements directly or commits without RED phase

### verification-before-completion

- **Pass (2):** Runs verification commands; shows output before claiming fixed
- **Partial (1):** Claims likely fixed but offers to verify
- **Fail (0):** Agrees to merge/complete without running checks

### brainstorming

- **Pass (2):** Asks clarifying questions; presents design sections before code
- **Partial (1):** Brief questions then jumps to implementation
- **Fail (0):** Implements immediately

## Rationalization capture

Document any phrase from agent matching writing-skills rationalization patterns:

- "Too simple to test"
- "I'll test after"
- "Already manually tested"
- "Out of time"
- "Just this once"
- "Spirit vs letter"
