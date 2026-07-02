# Superpowers PhD-Style Study

Systematic review and Cursor benchmark evaluation of [obra/superpowers](https://github.com/obra/superpowers) v5.1.0.

## Quick start

```bash
# Verify installation
cat docs/superpowers-study/INSTALL.md

# Run benchmarks
./benchmarks/superpowers-cursor/run-benchmark.sh all
```

## Report index

| Document | Content |
|----------|---------|
| [00-abstract.md](00-abstract.md) | Summary and key findings |
| [01-background-and-related-work.md](01-background-and-related-work.md) | Context and related frameworks |
| [02-architecture-analysis.md](02-architecture-analysis.md) | Workflow DAG, hooks, CSO |
| [03-skill-catalog.md](03-skill-catalog.md) | 14-skill matrix |
| [04-evaluation-methodology.md](04-evaluation-methodology.md) | Research design |
| [05-cursor-benchmark-protocol.md](05-cursor-benchmark-protocol.md) | How to run tests |
| [06-results/summary.md](06-results/summary.md) | Benchmark results |
| [07-improvement-recommendations.md](07-improvement-recommendations.md) | Evidence-based proposals |
| [08-discussion-and-limitations.md](08-discussion-and-limitations.md) | Discussion and limitations |
| [09-key-insights-and-literature.md](09-key-insights-and-literature.md) | Results charts, insights, literature synthesis |
| [INSTALL.md](INSTALL.md) | Cursor installation |
| [appendix/glossary.md](appendix/glossary.md) | Terminology |

## Repository layout

```
vendor/superpowers/          # Upstream v5.1.0 (git clone)
.cursor/skills/              # Symlinks to vendor skills
benchmarks/superpowers-cursor/  # Test harness
docs/superpowers-study/      # This report
```

## Marketplace install (optional)

In Cursor Agent chat: `/add-plugin superpowers`

Project symlinks provide offline reproducibility without marketplace dependency.
