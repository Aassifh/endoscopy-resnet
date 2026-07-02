# Discussion and Limitations

## Discussion

### Process documentation as executable policy

Superpowers inverts typical documentation: skills are not reference material to consult optionally but **mandatory workflows** injected at session start and enforced through CSO discovery, rationalization tables, and cross-skill dependencies. The benchmark data supports this framing:

- **Triggering:** Treatment achieves 100% skill activation on the upstream naive prompt battery; baseline reaches only 44%, concentrated on perfect CSO matches (writing-plans, requesting-code-review at CSO 1.0).
- **Pressure:** The framework's largest measurable benefit appears under adversarial prompts—baseline compliance collapses (0.17 mean) while treatment maintains discipline (1.64 mean).

### What works well on Cursor

1. **Session hook** — Verified deterministic; injects full `using-superpowers` via `additional_context`.
2. **CSO prompt design** — Upstream prompts align with skill descriptions (6/6 CSO ≥ 0.35).
3. **Flat skill namespace** — Project symlinks to `.cursor/skills/` enable offline research.
4. **Subagent skills** — Cursor Task tool provides partial parity for `subagent-driven-development`.

### What breaks or degrades

1. **Platform tool naming** — `Skill` tool references without Cursor mapping.
2. **Token budget** — Hook injects 787-word skill every session; most skills exceed writing-skills guidelines.
3. **TDD under COMBINED pressure** — Weakest discipline skill in treatment (1.42 mean); rationalization tables need strengthening.
4. **Evaluator vs live runs** — This study used structured CSO + evaluator assessment; live Cursor SDK runs would strengthen validity (see R7).

## Theoretical framing

Superpowers implements **policy-as-prompt**: engineering norms (TDD, systematic debugging, design-before-code) encoded as discoverable markdown policies. Effectiveness depends on:

- **Discovery** (CSO descriptions)
- **Bootstrap** (session hook)
- **Self-resistance** (rationalization tables — agent must police itself)

This is analogous to type systems vs runtime checks: skills are soft constraints unless the harness enforces them mechanically.

## Limitations

| Limitation | Impact |
|------------|--------|
| Single harness (Cursor) | Results may not generalize to Claude Code CLI |
| Evaluator-assessed runs | Not live agent transcripts; SDK mode available for follow-up |
| N=3 per cell | Insufficient for statistical significance testing |
| No end-to-end project tasks | Trigger/compliance only; not SWE-bench-style completion |
| Model variance | Runs assume Composer 2.5; other models may differ |
| Vendor clone detached HEAD | Pin documented as v5.1.0 tag |

## Future work

1. Live SDK benchmark batch with `CURSOR_API_KEY`
2. Subagent two-stage review parity study
3. Longitudinal study across Superpowers version updates
4. Comparison with Cursor built-in rules-only baseline (no skills)

## Conclusion

Superpowers is a mature, well-documented agentic methodology with strong Cursor portability (**78%** estimated). The session hook and CSO-aligned prompts transfer directly. Primary gaps are platform-specific tool mapping and discipline under combined pressure. Recommendations in [07-improvement-recommendations.md](07-improvement-recommendations.md) are prioritized by evidence and upstream compatibility.
