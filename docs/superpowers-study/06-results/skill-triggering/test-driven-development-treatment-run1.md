# Run: test-driven-development / treatment / run 1

- **Date:** 2026-06-11
- **Model:** composer-2.5 (evaluator-assessed)
- **Trigger:** PASS
- **CSO score:** 0.60
- **Skills observed:** using-superpowers (hook), test-driven-development
- **First action:** Write failing test for email validation
- **Compliance score:** N/A (triggering test)
- **Notes:** Treatment hook boost compensates for sub-0.85 CSO; baseline runs failed trigger 2/3

## Prompt (verbatim)

```
I need to add a new feature to validate email addresses. It should:
- Check that there's an @ symbol
- Check that there's at least one character before the @
- Check that there's a dot in the domain part
- Return true/false

Can you implement this?
```

## Evaluator rationale

Prompt contains "implement" + "feature" → CSO match. With Superpowers enabled, session hook mandates skill check before response; TDD skill description matches "before writing implementation code."
