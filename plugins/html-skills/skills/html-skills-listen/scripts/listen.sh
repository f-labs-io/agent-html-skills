#!/usr/bin/env bash
# html-skills-listen — does all the bash work for the html-skills-listen
# skill, so the skill's SKILL.md shrinks to: (1) run this script, (2) arm
# Monitor on the printed LOG path, (3) save the Monitor task ID.
#
# Idempotent. Safe to call every time an interactive skill fires.
#
# Output is key=value lines on stdout, parseable by the agent:
#   STATUS=WEB              — Claude Code web session, server mode unavailable.
#   STATUS=ALREADY_RUNNING  — receiver already up for this session. URL printed.
#   STATUS=STARTED          — receiver just started. URL + LOG + MIDF printed.
#   STATUS=ERROR            — startup failed. ERROR=<reason>; raw log dumped.
#
# Self-locating: the script finds server.js at $SCRIPT_DIR/../server.js, so
# it works regardless of whether CLAUDE_PLUGIN_ROOT is in the environment.
# Honored env: CLAUDE_CODE_SESSION_ID, CLAUDE_CODE_REMOTE_SESSION_ID.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
SERVER_JS="$SKILL_DIR/server.js"

SID="${CLAUDE_CODE_SESSION_ID:-no-session}"
PIDF=/tmp/html-skills-$SID.pid
LOGF=/tmp/html-skills-$SID.log
URLF=/tmp/html-skills-$SID.url
MIDF=/tmp/html-skills-$SID.monitor-id

echo "SID=$SID"
echo "LOG=$LOGF"
echo "MIDF=$MIDF"

# Web-mode short-circuit.
if [ -n "${CLAUDE_CODE_REMOTE_SESSION_ID:-}" ]; then
  echo "STATUS=WEB"
  exit 0
fi

# Idempotency: receiver already alive for this session.
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null && [ -s "$URLF" ]; then
  echo "STATUS=ALREADY_RUNNING"
  echo "URL=$(cat "$URLF")"
  exit 0
fi

# Opportunistic cleanup of stale dead-session files (silent no-op if nothing).
for f in /tmp/html-skills-*.pid; do
  [ -f "$f" ] || continue
  [ "$f" = "$PIDF" ] && continue
  P=$(cat "$f" 2>/dev/null)
  if [ -z "$P" ] || ! kill -0 "$P" 2>/dev/null; then
    base=${f%.pid}
    rm -f "$base.pid" "$base.log" "$base.url" "$base.monitor-id"
  fi
done

if [ ! -f "$SERVER_JS" ]; then
  echo "STATUS=ERROR"
  echo "ERROR=cannot-find-server-js at $SERVER_JS"
  exit 1
fi

# Start the receiver on an ephemeral port. HTML_SKILLS_CHANNEL_PORT=0 makes
# Node pick an open one.
: > "$LOGF"
HTML_SKILLS_CHANNEL_PORT=0 nohup node "$SERVER_JS" > "$LOGF" 2>&1 </dev/null &
echo $! > "$PIDF"
sleep 0.5

# Verify it's alive.
PID=$(cat "$PIDF")
if ! kill -0 "$PID" 2>/dev/null; then
  echo "STATUS=ERROR"
  echo "ERROR=receiver-died-on-startup"
  echo "--- log ---"
  cat "$LOGF"
  exit 1
fi

# Parse the chosen URL out of the receiver's log.
URL=$(grep -oE 'listening on http://127\.0\.0\.1:[0-9]+/' "$LOGF" | tail -1 \
      | sed 's/listening on //')
if [ -z "$URL" ]; then
  echo "STATUS=ERROR"
  echo "ERROR=no-listening-line-in-log"
  echo "--- log ---"
  cat "$LOGF"
  exit 1
fi
echo "$URL" > "$URLF"

echo "STATUS=STARTED"
echo "URL=$URL"
