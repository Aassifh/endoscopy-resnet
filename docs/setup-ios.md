# Mobile / iOS workflow — endoscopy-resnet

Use this repo from your iPhone in three layers (pick what you need).

## 1. Cursor Cloud Agents (best for “iterate with AI”)

Works from **Safari on iOS** — no app install required.

1. Push this repo to GitHub (once): `bash scripts/setup_mobile_github.sh`
2. Open [cursor.com/agents](https://cursor.com/agents) on your phone.
3. Connect GitHub account → select `endoscopy-resnet`.
4. Send tasks in natural language, e.g.:
   - “Run smoke benchmark and summarize JSON results”
   - “Update the French paper discussion with new C4 numbers”
   - “Add private center data prep for LOO fold”

Agents run in the cloud on your repo; you review diffs and merge on GitHub mobile.

## 2. GitHub mobile app (review + trigger runs)

Install **GitHub** from the App Store.

| Action | How |
|--------|-----|
| Read code / diffs | Repo → Files or Pull requests |
| Merge agent PRs | Pull requests → Review → Merge |
| CI status | Actions tab → latest `CI` workflow |
| Start benchmarks on your Mac | Actions → **Benchmark (self-hosted Mac)** → Run workflow → choose `smoke` / `resume` / `force` |

Cloud CI (`CI` workflow) runs unit tests on every push — no GPU needed.

Full JEPA campaigns need your **Mac online** with a self-hosted runner (section 3).

## 3. Self-hosted runner on your Mac (GPU benchmarks from phone)

One-time setup on the Mac that has MPS/GPU:

```bash
# In GitHub: Repo → Settings → Actions → Runners → New self-hosted runner → macOS
# Then on your Mac:
cd ~/actions-runner   # or path from GitHub instructions
./config.sh --url https://github.com/YOUR_USER/endoscopy-resnet --token TOKEN
./run.sh
```

Add label `macos-mps` when prompted (must match `.github/workflows/benchmark-selfhosted.yml`).

Keep the runner alive:

- **Tailscale** on Mac + iPhone → you can SSH/fix runner remotely.
- Or **launchd** service (see `scripts/install_github_runner_service.sh` stub below).

From iPhone: GitHub app → Actions → **Benchmark (self-hosted Mac)** → Run workflow.

Results appear as **Artifacts** (download `benchmark-results-*.zip` on phone).

## 4. Git on iOS (optional, small edits)

**Working Copy** (App Store): clone GitHub repo, edit markdown/scripts, commit, push.

Good for:
- Tweaking `docs/paper/fr/sections/*.tex`
- Updating `benchmarks/ml/results/*.json` notes
- README / protocol edits

Not good for: training (needs Mac or cloud GPU).

## 5. SSH to your Mac (power users)

1. Install **Tailscale** on Mac + iPhone (same account).
2. Install **Termius** or **Blink Shell** on iPhone.
3. SSH: `ssh user@<tailscale-ip>`
4. Run locally:
   ```bash
   cd ~/perso/endoscopy-resnet
   pixi run run-jepa-campaign
   bash scripts/run_article_campaign_loop.sh --status
   make -C docs/paper all
   ```

## Quick reference

| Goal | Tool |
|------|------|
| AI coding from phone | Cursor Cloud Agents + GitHub |
| Trigger smoke CI | Push branch / open PR |
| Long GPU benchmark | Self-hosted runner + GitHub Actions dispatch |
| Edit tex/md | Working Copy |
| Shell on Mac | Tailscale + Termius |

## One-shot GitHub setup

```bash
bash scripts/setup_mobile_github.sh
```

Creates the remote repo (if needed), initial commit, and push to `main`.

## Data & checkpoints

Not in git (too large). On Mac only:

- `data/` — download via `pixi run prepare-kvasir` etc.
- `checkpoints/` — produced by training

For mobile iteration you typically work on **code + docs + JSON results**; retrain on Mac when home.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Agent can’t see private data | Expected — add samples or document paths in issue |
| Self-hosted job queued forever | Mac asleep or runner not running — wake Mac, `./run.sh` |
| CI fails on Linux | Project dev is macOS+MPS; CI is smoke-only by design |
| Paper build on phone | Use Mac SSH or ask Cloud Agent; needs `tectonic` |
