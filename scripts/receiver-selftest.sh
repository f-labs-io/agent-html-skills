#!/usr/bin/env bash
# Exercise the html-skills receiver end to end, without Claude Code:
#   start → idempotent re-run → valid POST → forged POST (403) → three aborted
#   requests (receiver must survive) → POST again → kill -9 and restart (same URL
#   reused) → restart with the port busy (handshake reused, PORT_CHANGED=1) → stop.
#
# Usage: scripts/receiver-selftest.sh
# Needs: node, curl, python3. Uses a throwaway session id; never touches a live session.
# Exit 0 when every step behaves; 1 on the first failure.

set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.."
L=plugins/html-skills/skills/html-skills-listen/scripts/listen.sh
T=plugins/html-skills/skills/html-skills-stop/scripts/stop.sh
SID="selftest-$$"
fail() { echo "FAIL: $*"; bash "$T" "$SID" >/dev/null 2>&1; exit 1; }
mask() { sed -E 's/(t=)[0-9a-f]+/\1<handshake>/'; }
post() { curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' \
  -d '{"skill":"selftest","kind":"t","data":{"n":1},"version":1}' "$1"; }
abort() { python3 - "$1" <<'PY'
import socket, sys, urllib.parse
u = urllib.parse.urlsplit(sys.argv[1])
s = socket.create_connection((u.hostname, u.port))
s.sendall(f"POST {u.path}?{u.query} HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nContent-Length: 1000\r\n\r\n{{\"partial\":".encode())
s.close()
PY
}
port_of() { printf '%s' "$1" | sed -nE 's#^http://127\.0\.0\.1:([0-9]+)/.*#\1#p'; }
token_of() { printf '%s' "$1" | sed -nE 's#.*[?&]t=([0-9a-f]+).*#\1#p'; }

echo "== start"
out=$(bash "$L" "$SID"); echo "$out" | mask
echo "$out" | grep -q '^STATUS=STARTED$' || fail "expected STATUS=STARTED"
URL=$(echo "$out" | sed -n 's/^URL=//p'); PIDF=/tmp/html-skills-$SID.pid

echo "== idempotent re-run"
bash "$L" "$SID" | grep -q '^STATUS=ALREADY_RUNNING$' || fail "expected ALREADY_RUNNING"

echo "== valid POST"; [ "$(post "$URL")" = 200 ] || fail "valid POST not 200"
echo "== forged POST (no handshake)"; [ "$(post "${URL%%\?*}")" = 403 ] || fail "forged POST not 403"

echo "== three aborted requests"
abort "$URL"; abort "$URL"; abort "$URL"; sleep 0.5
kill -0 "$(cat "$PIDF")" 2>/dev/null || fail "receiver died after an aborted request"
[ "$(post "$URL")" = 200 ] || fail "POST after aborts not 200"

echo "== kill -9, then restart"
kill -9 "$(cat "$PIDF")"; sleep 0.3
out2=$(bash "$L" "$SID")
echo "$out2" | grep -q '^RESTARTED=1$' || fail "expected RESTARTED=1"
[ "$(echo "$out2" | sed -n 's/^URL=//p')" = "$URL" ] || fail "restart did not reuse the URL"
[ "$(post "$URL")" = 200 ] || fail "original URL not accepted after restart"

echo "== restart with the port busy"
kill -9 "$(cat "$PIDF")"; sleep 0.3
PORT=$(port_of "$URL")
python3 -c "import socket,time; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('127.0.0.1',$PORT)); s.listen(1); time.sleep(15)" &
OCC=$!; sleep 0.4
out3=$(bash "$L" "$SID"); kill "$OCC" 2>/dev/null
echo "$out3" | grep -q '^PORT_CHANGED=1$' || fail "expected PORT_CHANGED=1"
URL3=$(echo "$out3" | sed -n 's/^URL=//p')
[ "$(token_of "$URL")" = "$(token_of "$URL3")" ] || fail "handshake not reused on the new port"
[ "$(post "$URL3")" = 200 ] || fail "POST to the new URL not 200"

echo "== stop"
bash "$T" "$SID" | grep -q '^STATUS=STOPPED$' || fail "expected STATUS=STOPPED"
ls /tmp/html-skills-"$SID".* >/dev/null 2>&1 && fail "temp files left behind"

echo "OK: receiver self-test passed"
