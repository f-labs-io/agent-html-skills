#!/usr/bin/env bash
# html-skills-listen — starts (or finds) this session's submit receiver, so the
# skill's SKILL.md shrinks to: (1) run this script, (2) arm Monitor on the printed
# LOG path, (3) save the Monitor task id.
#
# Usage: listen.sh [session-id]
#   The session id comes from Claude Code's ${CLAUDE_SESSION_ID} substitution;
#   falls back to $CLAUDE_CODE_SESSION_ID, then "no-session".
#
# Idempotent. Safe to call every time a content skill fires.
#
# Output is KEY=VALUE lines on stdout:
#   STATUS=WEB              — Claude Code web session, server mode unavailable.
#   STATUS=ALREADY_RUNNING  — receiver already up for this session. URL printed.
#   STATUS=STARTED          — receiver started. URL + LOG + MIDF printed.
#                             RESTARTED=1 when a previous receiver for this session
#                             had died (its handshake value is reused so earlier
#                             artifacts keep working); PORT_CHANGED=1 when that
#                             previous port was busy and an ephemeral one was used.
#   STATUS=ERROR            — startup failed. ERROR=<reason>; raw log dumped.
#
# Self-locating: server.js is resolved next to this script, so nothing here
# depends on CLAUDE_PLUGIN_ROOT being in the environment.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
SERVER_JS="$SKILL_DIR/server.js"

SID="${1:-${CLAUDE_CODE_SESSION_ID:-no-session}}"
PIDF=/tmp/html-skills-$SID.pid
LOGF=/tmp/html-skills-$SID.log
URLF=/tmp/html-skills-$SID.url
MIDF=/tmp/html-skills-$SID.monitor-id

echo "SID=$SID"
echo "LOG=$LOGF"
echo "MIDF=$MIDF"

# Web-mode short-circuit: the sandbox can't reach the user's browser.
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

# Opportunistic cleanup of other, dead sessions' files (silent no-op if none).
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

if ! command -v node >/dev/null 2>&1; then
  echo "STATUS=ERROR"
  echo "ERROR=node-not-found (the receiver is a zero-dependency Node script; install Node.js or use clipboard mode)"
  exit 1
fi

# Restart support: if a URL file survives from a receiver that died, reuse its
# handshake value (and its port when free) so artifacts generated earlier this
# session keep submitting successfully.
PREV_URL=""
[ -s "$URLF" ] && PREV_URL=$(cat "$URLF")
PREV_PORT=""
PREV_TOKEN=""
if [ -n "$PREV_URL" ]; then
  PREV_PORT=$(printf '%s' "$PREV_URL" | sed -nE 's#^http://127\.0\.0\.1:([0-9]+)/.*#\1#p')
  PREV_TOKEN=$(printf '%s' "$PREV_URL" | sed -nE 's#.*[?&]t=([0-9a-f]+).*#\1#p')
fi

: > "$LOGF"
if [ -n "$PREV_TOKEN" ]; then
  HTML_SKILLS_CHANNEL_PORT="${PREV_PORT:-0}" HTML_SKILLS_CHANNEL_TOKEN="$PREV_TOKEN" HTML_SKILLS_PORT_FALLBACK=1 \
    nohup node "$SERVER_JS" > "$LOGF" 2>&1 </dev/null &
else
  HTML_SKILLS_CHANNEL_PORT=0 nohup node "$SERVER_JS" > "$LOGF" 2>&1 </dev/null &
fi
echo $! > "$PIDF"

# Wait for the listening line (up to ~3s) instead of a fixed sleep.
PID=$(cat "$PIDF")
i=0
while [ "$i" -lt 30 ]; do
  grep -q 'listening on http://127\.0\.0\.1:' "$LOGF" 2>/dev/null && break
  kill -0 "$PID" 2>/dev/null || break
  sleep 0.1
  i=$((i + 1))
done

if ! kill -0 "$PID" 2>/dev/null; then
  echo "STATUS=ERROR"
  echo "ERROR=receiver-died-on-startup"
  echo "--- log ---"
  cat "$LOGF"
  exit 1
fi

# The URL carries the per-session loopback handshake as its `?t=` query string.
# Capture it whole; the receiver rejects any POST that doesn't present it.
URL=$(grep -oE 'listening on http://127\.0\.0\.1:[0-9]+/\?t=[^[:space:]]+' "$LOGF" | tail -1 \
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
if [ -n "$PREV_URL" ]; then
  echo "RESTARTED=1"
  NEW_PORT=$(printf '%s' "$URL" | sed -nE 's#^http://127\.0\.0\.1:([0-9]+)/.*#\1#p')
  [ "$NEW_PORT" != "$PREV_PORT" ] && echo "PORT_CHANGED=1"
fi
exit 0
