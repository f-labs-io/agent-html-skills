#!/usr/bin/env bash
# html-skills-stop — kills this session's html-skills receiver and cleans up
# its temp files. The Monitor task ID lives in /tmp/html-skills-$SID.monitor-id
# and must be stopped by the agent via TaskStop, since Monitor is a
# Claude Code tool, not a shell concept — the script prints the ID and the
# parent SKILL.md does the TaskStop call.
#
# Output: KEY=VALUE lines.
#   STATUS=WEB         — nothing was running here; web session.
#   STATUS=INACTIVE    — no PID file; nothing to kill.
#   STATUS=STOPPED     — receiver killed, files cleaned. MONITOR_ID printed if
#                        there was one saved (parent skill should TaskStop it).

set -u

SID="${CLAUDE_CODE_SESSION_ID:-no-session}"
PIDF=/tmp/html-skills-$SID.pid
LOGF=/tmp/html-skills-$SID.log
URLF=/tmp/html-skills-$SID.url
MIDF=/tmp/html-skills-$SID.monitor-id

echo "SID=$SID"

if [ -n "${CLAUDE_CODE_REMOTE_SESSION_ID:-}" ]; then
  echo "STATUS=WEB"
  exit 0
fi

if [ ! -f "$PIDF" ]; then
  echo "STATUS=INACTIVE"
  exit 0
fi

# Print the Monitor task ID first (parent SKILL.md will TaskStop it).
if [ -s "$MIDF" ]; then
  echo "MONITOR_ID=$(cat "$MIDF")"
fi

# Kill the receiver.
PID=$(cat "$PIDF")
kill "$PID" 2>/dev/null || true

# Clean up files.
rm -f "$PIDF" "$LOGF" "$URLF" "$MIDF"

echo "STATUS=STOPPED"
