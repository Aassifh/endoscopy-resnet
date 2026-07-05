#!/usr/bin/env bash
# Start full publication pipeline via launchd (or nohup fallback).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FORCE=false
INIT=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=true; shift ;;
    --init) INIT=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

LOG="benchmarks/ml/results/publication_pipeline.log"
PIDFILE="benchmarks/ml/results/publication_pipeline.pid"
WORKER="$ROOT/scripts/run_publication_pipeline_worker.sh"
LABEL="com.endoscopy-resnet.publication-pipeline"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
mkdir -p benchmarks/ml/results "$HOME/Library/LaunchAgents"

chmod +x "$WORKER"

if $INIT; then
  bash "$WORKER" --init
  exit 0
fi

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE")"
  kill -0 "$old_pid" 2>/dev/null && kill "$old_pid" 2>/dev/null || true
fi

if $FORCE; then
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${WORKER}</string>
    <string>--force</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>${ROOT}/benchmarks/ml/results/publication_pipeline.log</string>
  <key>StandardErrorPath</key>
  <string>${ROOT}/benchmarks/ml/results/publication_pipeline.log</string>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
EOF
else
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${WORKER}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>${ROOT}/benchmarks/ml/results/publication_pipeline.log</string>
  <key>StandardErrorPath</key>
  <string>${ROOT}/benchmarks/ml/results/publication_pipeline.log</string>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
EOF
fi

if ! launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null; then
  echo "launchctl bootstrap failed; falling back to nohup"
  : >> "$LOG"
  nohup bash "$WORKER" ${FORCE:+--force} >>"$LOG" 2>&1 &
  echo $! > "$PIDFILE"
  echo "Started via nohup (pid $(cat "$PIDFILE"))"
else
  echo 0 > "$PIDFILE"
  echo "Started via launchd ($LABEL)"
fi

echo "Log: $LOG"
echo "State: benchmarks/ml/results/publication_pipeline_state.json"
echo "Stop: launchctl bootout gui/$(id -u)/$LABEL"
