# Mobile / iOS workflow — endoscopy-resnet

> **Use Cursor on iPhone?** Start here: **[docs/setup-cursor-ios.md](setup-cursor-ios.md)** (Cursor iOS app, Cloud Agents, Remote Control, My Machines).

This page covers **GitHub Actions** and generic git/SSH fallbacks.

---

## Cursor iOS (recommended)

1. Install [Cursor from the App Store](https://apps.apple.com/app/cursor/id6767085653).
2. Connect GitHub in [Cursor Dashboard](https://cursor.com/dashboard) → repo **`Aassifh/endoscopy-resnet`**.
3. New agent → **Cloud** (code/docs) or **My Machines** (GPU benchmarks on your Mac).
4. See **[setup-cursor-ios.md](setup-cursor-ios.md)** for prompts and Remote Control (`/remote-control`).

---

## GitHub mobile app (optional)

| Action | How |
|--------|-----|
| Merge agent PRs | Pull requests → Review → Merge |
| CI status | Actions → `CI` workflow |
| Trigger Mac benchmarks | Actions → **Benchmark (self-hosted Mac)** → Run workflow |

---

## Self-hosted runner (GPU from GitHub app)

```bash
bash scripts/install_github_runner.sh
cd ~/actions-runners/endoscopy-resnet && ./run.sh
```

---

## Repo URL

https://github.com/Aassifh/endoscopy-resnet
