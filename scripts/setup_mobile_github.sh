#!/usr/bin/env bash
# One-shot: init git, create GitHub repo, push main — enables iOS / Cursor Cloud Agents.
#
# Usage:
#   bash scripts/setup_mobile_github.sh
#   bash scripts/setup_mobile_github.sh --private
#   bash scripts/setup_mobile_github.sh --repo-name my-fork

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PRIVATE=false
REPO_NAME="endoscopy-resnet"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --private) PRIVATE=true; shift ;;
    --repo-name) REPO_NAME="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

if ! command -v gh >/dev/null; then
  echo "Install GitHub CLI: brew install gh && gh auth login"
  exit 1
fi

gh auth status >/dev/null

if [[ ! -d .git ]]; then
  git init -b main
fi

if ! git rev-parse HEAD >/dev/null 2>&1; then
  git add -A
  git commit -m "$(cat <<'EOF'
Initial commit: endoscopy-resnet pipeline and CNN-JEPA benchmarks.

Includes ResNet/SE-ResNet training, JEPA pretrain, C0-C10 campaign scripts,
LaTeX papers (EN/FR), and mobile/GitHub Actions workflow docs.
EOF
)"
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote origin already set:"
  git remote -v
else
  VIS="--public"
  $PRIVATE && VIS="--private"
  gh repo create "$REPO_NAME" $VIS --source=. --remote=origin --push --description \
    "SE-ResNet + CNN-JEPA colonoscopy classification — train, benchmark, paper"
  echo "Created and pushed: $(gh repo view --json url -q .url)"
  exit 0
fi

echo "Pushing to origin..."
git push -u origin main
echo "Done: $(gh repo view --json url -q .url 2>/dev/null || echo origin)"

echo ""
echo "Next on iPhone:"
echo "  1. GitHub app → clone $(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo USER/$REPO_NAME)"
echo "  2. Safari → cursor.com/agents → connect repo"
echo "  3. See docs/setup-ios.md for self-hosted benchmark runner"
