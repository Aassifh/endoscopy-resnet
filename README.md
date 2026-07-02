# endoscopy-resnet

Colonoscopy frame classification: ResNet / SE-ResNet, CNN-JEPA pretraining, benchmarks C0–C10, LaTeX papers (EN/FR).

## Quick start (Mac)

```bash
pixi install
pixi run prepare-colonoscopy-3class
pixi run run-jepa-campaign          # one benchmark job at a time
make -C docs/paper all              # compile EN/FR papers
```

## Use from iPhone (iOS)

See **[docs/setup-ios.md](docs/setup-ios.md)** for the full guide.

1. **One-time:** push to GitHub  
   ```bash
   bash scripts/setup_mobile_github.sh
   ```
2. **Cursor Cloud Agents:** [cursor.com/agents](https://cursor.com/agents) → connect repo → iterate from Safari.
3. **GitHub app:** review PRs, trigger **Benchmark (self-hosted Mac)** workflow (Mac must run a GitHub Actions runner with label `macos-mps`).

## Docs

| Path | Content |
|------|---------|
| [docs/setup-ios.md](docs/setup-ios.md) | Mobile / iOS workflow |
| [benchmarks/ml/protocol.md](benchmarks/ml/protocol.md) | C0–C10 protocol |
| [docs/paper/](docs/paper/) | LaTeX manuscripts EN + FR |
| [benchmarks/ml/results/jepa_summary.md](benchmarks/ml/results/jepa_summary.md) | Latest JEPA results |

## Author

Hamza AASSIF — `hamza@dynvibe.com`
