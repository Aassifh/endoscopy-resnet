# endoscopy-resnet

Colonoscopy frame classification: ResNet / SE-ResNet, CNN-JEPA pretraining, benchmarks C0–C10, LaTeX papers (EN/FR).

## Quick start (Mac)

```bash
pixi install
pixi run prepare-colonoscopy-3class
pixi run run-jepa-campaign          # one benchmark job at a time
make -C docs/paper all              # compile EN/FR papers
```

## Use from iPhone (Cursor)

**→ [docs/setup-cursor-ios.md](docs/setup-cursor-ios.md)** — Cursor iOS app, Cloud Agents, My Machines, Remote Control.

Repo: https://github.com/Aassifh/endoscopy-resnet

1. Install **Cursor** (App Store) → sign in → pick this repo → start an agent.
2. **Cloud worker:** edit code/docs, tests, LaTeX, open PRs (Mac can be off).
3. **My Machines:** run `pixi` / JEPA benchmarks on your Mac from your phone.
4. **Remote Control:** type `/remote-control` on Mac → continue session on iPhone.

Fallback (GitHub Actions): [docs/setup-ios.md](docs/setup-ios.md)

## Docs

| Path | Content |
|------|---------|
| [docs/setup-ios.md](docs/setup-ios.md) | Mobile / iOS workflow |
| [benchmarks/ml/protocol.md](benchmarks/ml/protocol.md) | C0–C10 protocol |
| [docs/paper/](docs/paper/) | LaTeX manuscripts EN + FR |
| [benchmarks/ml/results/jepa_summary.md](benchmarks/ml/results/jepa_summary.md) | Latest JEPA results |

## Author

Hamza AASSIF — `hamza@dynvibe.com`
