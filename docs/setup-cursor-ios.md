# Cursor on iPhone — endoscopy-resnet

Use this repo from your **Cursor iOS app** (not a code editor — an **agent remote**).

**Repo:** https://github.com/Aassifh/endoscopy-resnet  
**Requires:** Cursor Pro+ (cloud agents), iOS 26+, GitHub connected in Cursor Dashboard.

---

## 1. Install & connect (5 min)

1. **App Store** → install [Cursor](https://apps.apple.com/app/cursor/id6767085653).
2. Sign in with your **Cursor account** (same as desktop).
3. **Dashboard** (once on Mac/web): [cursor.com/dashboard](https://cursor.com/dashboard) → connect **GitHub** → grant access to `Aassifh/endoscopy-resnet`.
4. **Privacy:** Cloud Agents need **Privacy Mode** (not Legacy). The app will prompt you to switch on first use.
5. In the iOS app → **New agent** → pick repo **`Aassifh/endoscopy-resnet`** → branch **`main`**.

---

## 2. Three ways to iterate from your phone

**Start here if Remote Control is missing** (common): use **A** or **B**.

### A) Cloud agent (Mac can be off)

Best for: docs, scripts, small refactors, reading benchmark JSON, updating LaTeX.

1. Cursor iOS → New agent → worker: **Cloud**.
2. Example prompts:
   - *“Read benchmarks/ml/results/jepa_summary.md and update docs/paper/fr/sections/results.tex discussion.”*
   - *“Run pytest tests/ and fix any failure. Open a PR.”*
   - *“Add a prepare script option for polyp subtypes as future work in the FR paper.”*
3. Agent runs in Cursor’s cloud VM (installs deps, runs tests, opens PR).
4. **Review & merge** the PR from the app (diff view + squash merge).

**Note:** Large datasets (`data/kvasir`, `checkpoints/`) are **not in git**. Cloud agents cannot train on full HyperKvasir unless you add data or document download steps.

### B) My Machines / your Mac (GPU + pixi) — **recommended**

Best for: `pixi run pretrain-jepa`, full benchmark campaign, MPS training. **No Remote Control needed.**

1. **On Mac:** [cursor.com/dashboard](https://cursor.com/dashboard) → **Cloud Agents** → **My Machines** → add this Mac.
2. Keep Mac **awake & online** (System Settings → prevent sleep when plugged in).
3. Cursor iOS → New agent → worker: **My Machines** → select your Mac.
4. Example prompts:
   - *“Run bash scripts/run_article_campaign_loop.sh --smoke and summarize JSON in benchmarks/ml/results/.”*
   - *“Regenerate paper tables and compile docs/paper with tectonic.”*

Tool calls run **on your Mac**; you steer from the phone.

### C) Remote Control (optional — often not available yet)

**Important:** Remote Control is **not** in `Cursor Settings` (gear icon). Per [Cursor docs](https://cursor.com/docs/cloud-agent/mobile), the toggle lives only in the **Agents Window**, and it may **not appear yet** on all accounts (gradual rollout).

If you don't see it, **skip this section** — use **Cloud** or **My Machines** below instead (works for most people).

When available:

1. Open the **Agents** panel/window (not the regular chat sidebar).
2. In **that** panel: gear / Settings → **Agents** → enable **Remote Control**.
3. Needs Cursor **≥ 3.9.8**, paid plan, **Privacy Mode** (not Legacy), git remote on the repo.
4. In an agent chat on Mac, send: `/remote-control`
5. Session appears in the **Cursor iOS inbox**.

**Teams/Enterprise:** admin must enable it in Dashboard → Cloud Agents → Self-Hosted.

---

## 3. Prompts tailored to this project

Copy-paste into Cursor iOS:

| Goal | Prompt |
|------|--------|
| Status | `Read benchmarks/ml/results/jepa_campaign_state.json and jepa_summary.md; summarize what's done and pending.` |
| Smoke test | `On My Machine: pixi install && bash scripts/run_article_campaign_loop.sh --smoke` |
| Paper EN | `Run python scripts/generate_paper_tables.py && make -C docs/paper en` |
| Paper FR | `Update docs/paper/fr/sections/discussion.tex with latest C1 vs C4 numbers from jepa_summary.md` |
| New experiment | `Add LOO fold for a new private center under data/private/center_a/labeled/ and extend prepare_colonoscopy_3class.py` |

Project context for agents: see **[AGENTS.md](../AGENTS.md)** at repo root.

---

## 4. What works well / what doesn’t on phone

| Works | Doesn’t (use My Machine or Mac desktop) |
|-------|----------------------------------------|
| Edit code, docs, LaTeX | Full HyperKvasir download (~4 GB) |
| Run unit tests (cloud CI too) | 24h JEPA campaign without Mac online |
| Review & merge PRs | Heavy MPS training in cloud worker |
| Voice input for prompts | Editing `.pixi/env` interactively |
| Push notifications when agent done | Local `data/` symlinks on Mac only |

---

## 5. Desktop ↔ mobile sync

- Agents started on **phone** appear in desktop **Cloud Agents** panel and [cursor.com/agents](https://cursor.com/agents).
- Agents started on **desktop** appear in the **iOS inbox** automatically.
- Use **`/remote-control`** to hand off a local session to your phone (only if that feature is enabled on your account).

---

## 6. Troubleshooting

| Problem | Fix |
|---------|-----|
| **No Remote Control in Settings** | Normal — it's only in the **Agents Window** settings, not global Settings; often not rolled out yet. Use **My Machines** or **Cloud** instead. |
| Repo not listed | GitHub not connected or repo not granted — fix in Cursor Dashboard |
| “Privacy Mode (Legacy)” | Switch to Privacy Mode in app prompt |
| My Machine unavailable | Mac asleep, offline, or not registered under Dashboard → Cloud Agents → My Machines |
| `/remote-control` unknown | Feature not on your build yet — update Cursor or use My Machines |
| Agent can’t train | Use **My Machines** (Mac with pixi/MPS), not Cloud worker |
| `data/` not found | Run on Mac: `pixi run prepare-colonoscopy-3class` |

---

## 7. Optional: GitHub Actions from phone

If you prefer triggering benchmarks without Cursor: GitHub app → Actions → **Benchmark (self-hosted Mac)**. See [setup-ios.md](setup-ios.md) for runner install (`scripts/install_github_runner.sh`).

---

## Links

- [Cursor for iOS docs](https://cursor.com/docs/cloud-agent/mobile)
- [Cloud agents setup](https://cursor.com/docs/cloud-agent/setup)
- [Blog: Cursor for iOS](https://cursor.com/blog/ios-mobile-app)
