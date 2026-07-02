#!/usr/bin/env bash
# Start JEPA campaign via launchd (survives IDE disconnect) or nohup fallback.
#
# Usage:
#   bash scripts/run_campaign_nohup.sh --force

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FORCE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

LOG="benchmarks/ml/results/jepa_campaign.nohup.log"
PIDFILE="benchmarks/ml/results/jepa_campaign.nohup.pid"
WORKER="$ROOT/scripts/run_campaign_nohup_worker.sh"
LABEL="com.endoscopy-resnet.jepa-campaign"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
mkdir -p benchmarks/ml/results "$HOME/Library/LaunchAgents"

chmod +x "$WORKER"

# Stop previous launchd job if any
launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  kill -0 "$old_pid" 2>/dev/null && kill "$old_pid" 2>/dev/null || true
fi

sed -e "s|REPO_ROOT|$ROOT|g" -e "s|WORKER_SCRIPT|$WORKER|g" \
  "$ROOT/scripts/com.endoscopy-resnet.jepa-campaign.plist.template" > "$PLIST"

ARGS=(launchctl bootstrap "gui/$(id -u)" "$PLIST")
if ! "${ARGS[@]}" 2>/dev/null; then
  echo "launchctl bootstrap failed; falling back to nohup"
  : > "$LOG"
  nohup bash "$WORKER" ${FORCE:+--force} >>"$LOG" 2>&1 &
  echo $! > "$PIDFILE"
  echo "Started via nohup (pid $(cat "$PIDFILE"))"
else
  echo 0 > "$PIDFILE"
  echo "Started via launchd ($LABEL)"
fi

echo "Log: $LOG"
echo "Tail: tail -f $LOG"
echo "Stop: launchctl bootout gui/$(id -u)/$LABEL 2>/dev/null; kill \$(cat $PIDFILE) 2>/dev/null"
