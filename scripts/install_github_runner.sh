#!/usr/bin/env bash
# Install GitHub Actions self-hosted runner (run once on your Mac).
# After install: label runner `macos-mps` when prompted.
#
# Usage:
#   bash scripts/install_github_runner.sh
#
# Get registration token from:
#   gh api repos/Aassifh/endoscopy-resnet/actions/runners/registration-token -X POST --jq .token

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNNER_DIR="$HOME/actions-runners/endoscopy-resnet"
REPO="${GITHUB_REPO:-Aassifh/endoscopy-resnet}"

mkdir -p "$(dirname "$RUNNER_DIR")"
cd "$(dirname "$RUNNER_DIR")"

if [[ ! -d "$RUNNER_DIR" ]]; then
  ARCH=$(uname -m)
  if [[ "$ARCH" == "arm64" ]]; then
    PKG="actions-runner-osx-arm64-2.321.0.tar.gz"
  else
    PKG="actions-runner-osx-x64-2.321.0.tar.gz"
  fi
  curl -o "$PKG" -L "https://github.com/actions/runner/releases/download/v2.321.0/$PKG"
  mkdir -p endoscopy-resnet && cd endoscopy-resnet
  tar xzf "../$PKG"
else
  cd "$RUNNER_DIR"
fi

TOKEN=$(gh api "repos/$REPO/actions/runners/registration-token" -X POST --jq .token)

./config.sh --url "https://github.com/$REPO" --token "$TOKEN" --labels macos-mps --unattended

echo ""
echo "Start runner:"
echo "  cd $RUNNER_DIR && ./run.sh"
echo ""
echo "From iPhone: GitHub app → Actions → Benchmark (self-hosted Mac) → Run workflow"
