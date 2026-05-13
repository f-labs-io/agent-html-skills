#!/usr/bin/env python3
"""Web-session probe: empirically check what POST paths reach the sandbox dev server.

Single-file. Run inside a Claude Code web session (or anywhere with a single
proxied dev server port). It serves one HTML page with three POST buttons:

  A. same-origin POST /submit            (expected to pass through proxy)
  B. same-origin POST /api/submit        (expected to be CSRF-blocked per #27792)
  C. cross-origin POST 127.0.0.1:8788/   (expected to fail — different host/port
                                          from the user's browser POV)

Every request that hits this server is logged on stdout. The page shows the
HTTP status / network error returned to the browser. After exercising all
three buttons, click "Copy diagnostic" — that produces a self-contained
JSON summary the user pastes back into the agent.

Run:
    python3 web-probe.py [--port 0] [--host 127.0.0.1]

If --port is 0 the OS picks a free port; in a CC web session that port is
the one you'll preview.
"""
from __future__ import annotations
import argparse, http.server, json, sys, threading, time
from pathlib import Path

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>html-skills web-session probe</title>
<style>
  :root { --bg:#0b0d10; --fg:#e6e8eb; --muted:#8a93a0; --ok:#7bd88f; --err:#ff7878; --card:#15181d; --line:#252a30; }
  * { box-sizing: border-box; }
  body { margin:0; padding:24px; background:var(--bg); color:var(--fg); font:15px/1.5 ui-sans-serif,system-ui,sans-serif; }
  h1 { margin:0 0 4px; font-size:20px; }
  p.lede { margin:0 0 24px; color:var(--muted); max-width:60ch; }
  .test { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; margin-bottom:14px; }
  .test h2 { margin:0 0 6px; font-size:15px; font-family:ui-monospace,monospace; }
  .test p { margin:0 0 12px; color:var(--muted); font-size:13.5px; }
  .row { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
  button { background:#2a3038; color:var(--fg); border:1px solid var(--line); border-radius:6px; padding:8px 14px; font:14px ui-sans-serif,system-ui,sans-serif; cursor:pointer; }
  button:hover { background:#343b44; }
  button.copy { background:#1f6feb; border-color:#1f6feb; color:#fff; }
  .result { font-family:ui-monospace,monospace; font-size:13px; padding:8px 10px; border-radius:6px; background:#0e1115; border:1px solid var(--line); white-space:pre-wrap; flex:1 1 320px; min-height:34px; }
  .result.ok { color:var(--ok); border-color:#1f3d28; }
  .result.err { color:var(--err); border-color:#3d1f1f; }
  .summary { background:#0e1115; border:1px solid var(--line); border-radius:10px; padding:16px; margin-top:18px; font-family:ui-monospace,monospace; font-size:12.5px; white-space:pre-wrap; }
  footer { color:var(--muted); font-size:12.5px; margin-top:18px; }
  code { background:#0e1115; padding:1px 5px; border-radius:4px; font-size:12.5px; }
</style>
</head>
<body>
  <h1>html-skills web-session probe</h1>
  <p class="lede">Click each button. Each test posts a small JSON body to a different URL and records what the browser saw. The server also logs every request it received on stdout so we can compare browser-side vs sandbox-side. The goal: figure out which submit paths actually reach the dev server when previewed through the Claude Code web proxy.</p>

  <div class="test" id="t-a">
    <h2>A. same-origin <code>POST /submit</code></h2>
    <p>If this works, server mode is viable in a CC web session and we could enable it for cloud sessions.</p>
    <div class="row">
      <button onclick="run('a','/submit')">Run test A</button>
      <div class="result" id="r-a">— not run yet —</div>
    </div>
  </div>

  <div class="test" id="t-b">
    <h2>B. same-origin <code>POST /api/submit</code></h2>
    <p>Issue #27792 reports the proxy CSRF-blocks <code>/api</code> POSTs with a 403. This test confirms or refutes that.</p>
    <div class="row">
      <button onclick="run('b','/api/submit')">Run test B</button>
      <div class="result" id="r-b">— not run yet —</div>
    </div>
  </div>

  <div class="test" id="t-c">
    <h2>C. cross-origin <code>POST http://127.0.0.1:8788/</code></h2>
    <p>Cross-origin to a different port (what an old "auto-discover :8788" probe would do). In CC web that hits the user's own machine, not the sandbox, so we expect a network error — and this is one of the reasons we removed auto-probing.</p>
    <div class="row">
      <button onclick="run('c','http://127.0.0.1:8788/')">Run test C</button>
      <div class="result" id="r-c">— not run yet —</div>
    </div>
  </div>

  <div class="row" style="margin-top:18px;">
    <button class="copy" onclick="copyDiag()">Copy diagnostic JSON</button>
    <div class="result" id="copy-status">paste it back into the agent</div>
  </div>

  <div class="summary" id="summary">{}</div>

  <footer>
    Probe page served by <code>web-probe.py</code>. Server-side request log goes to the agent's terminal stdout.
  </footer>

<script>
const results = { a:null, b:null, c:null, ts: new Date().toISOString(), origin: location.origin, href: location.href };

async function run(key, url) {
  const cell = document.getElementById('r-' + key);
  cell.className = 'result';
  cell.textContent = 'running…';
  const body = JSON.stringify({ probe: 'html-skills', test: key, t: Date.now() });
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 4000);
  let outcome;
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      signal: ctrl.signal,
    });
    let text = '';
    try { text = await r.text(); } catch (e) {}
    outcome = { ok: r.ok, status: r.status, statusText: r.statusText, body: text.slice(0, 200) };
    cell.className = 'result ' + (r.ok ? 'ok' : 'err');
    cell.textContent = `${r.status} ${r.statusText}\\n${text.slice(0, 200)}`;
  } catch (e) {
    outcome = { ok: false, error: String(e), name: e.name };
    cell.className = 'result err';
    cell.textContent = `network error: ${e.name} — ${e.message}`;
  } finally {
    clearTimeout(timeout);
  }
  results[key] = { url, ...outcome };
  document.getElementById('summary').textContent = JSON.stringify(results, null, 2);
}

async function copyDiag() {
  const status = document.getElementById('copy-status');
  const text = JSON.stringify(results, null, 2);
  try {
    await navigator.clipboard.writeText(text);
    status.className = 'result ok';
    status.textContent = 'copied — paste into the agent';
  } catch (e) {
    status.className = 'result err';
    status.textContent = 'clipboard blocked — copy from the box below';
    document.getElementById('summary').focus();
  }
}
</script>
</body>
</html>
"""


def make_handler(log: list, evt: threading.Event):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a, **kw):
            pass

        def _log(self, kind: str, extra: dict | None = None):
            entry = {
                't': time.strftime('%H:%M:%S'),
                'method': self.command,
                'path': self.path,
                'kind': kind,
                'origin': self.headers.get('Origin'),
                'referer': self.headers.get('Referer'),
                'ua': (self.headers.get('User-Agent') or '')[:80],
            }
            if extra:
                entry.update(extra)
            log.append(entry)
            print('REQ ' + json.dumps(entry, separators=(',', ':')), flush=True)

        def do_GET(self):
            if self.path in ('/', '/index.html'):
                self._log('page')
                data = PAGE.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if self.path == '/__diagnostic':
                data = json.dumps(log, indent=2).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self._log('404-get')
            self.send_error(404)

        def do_POST(self):
            n = int(self.headers.get('Content-Length', '0') or '0')
            raw = self.rfile.read(n) if n else b''
            try:
                body = raw.decode('utf-8')
            except Exception:
                body = '<binary>'
            self._log('post', {'body': body[:200]})
            if self.path in ('/submit', '/api/submit'):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True, 'echo_path': self.path}).encode())
                if self.path == '/submit' and body:
                    pass
                return
            self.send_error(404)

        def do_OPTIONS(self):
            self._log('options')
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.end_headers()

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=0)
    ap.add_argument('--host', default='127.0.0.1')
    args = ap.parse_args()

    log: list = []
    evt = threading.Event()
    server = http.server.ThreadingHTTPServer((args.host, args.port), make_handler(log, evt))
    actual_port = server.server_address[1]
    print(f'PORT={actual_port}', flush=True)
    print(f'URL=http://{args.host}:{actual_port}/', flush=True)
    print('listening — Ctrl-C to stop. Each request logs as REQ {...} below.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main())
