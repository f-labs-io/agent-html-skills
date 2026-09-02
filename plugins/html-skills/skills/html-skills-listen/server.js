#!/usr/bin/env node
/**
 * html-skills submit receiver.
 *
 * Receives submissions from interactive HTML artifacts produced by the
 * html-skills plugin. Started in the background by the `html-skills-listen`
 * skill's scripts/listen.sh, which lives alongside this file.
 *
 * How it works:
 *   - A localhost HTTP server on an ephemeral port (set HTML_SKILLS_CHANNEL_PORT
 *     to pin one). Every accepted POST body is written to stdout as ONE line:
 *       {"jsonrpc":"2.0","method":"notifications/claude/channel","params":{"content":<body>,"meta":{...}}}
 *     `html-skills-listen` arms a `Monitor` that tails this output filtered on
 *     `"method":"notifications/claude/channel"`, turning each line into a session
 *     notification for the agent. That line shape is the contract; keep it stable.
 *   - Security: binds to loopback only. Every POST must present the per-session
 *     loopback handshake value (random at startup unless HTML_SKILLS_CHANNEL_TOKEN
 *     is set), carried as `?t=` in the URL handed to the artifact or as an
 *     X-HTML-Skills-Token header. Requests without it are rejected with 403 before
 *     anything is forwarded, so other pages or local processes can't inject into
 *     the session. Bodies are capped at 256KB. Forwarded content is untrusted user
 *     data; the consuming agent treats it strictly as data, never as instructions.
 *   - Robustness: a client that disconnects mid-request must never take the
 *     receiver down (an artifact tab closed during Submit is normal), so request
 *     errors are caught and logged, and unhandled errors are logged, not fatal.
 *   - Restarts: listen.sh passes a previous receiver's handshake and port back in
 *     via HTML_SKILLS_CHANNEL_TOKEN / HTML_SKILLS_CHANNEL_PORT so artifacts generated
 *     before a restart keep working. With HTML_SKILLS_PORT_FALLBACK=1 a busy pinned
 *     port falls back to an ephemeral one instead of failing.
 *
 * Zero runtime dependencies.
 */

'use strict';

const http = require('node:http');
const crypto = require('node:crypto');

const PORT = parseInt(process.env.HTML_SKILLS_CHANNEL_PORT || '0', 10);
const HOST = '127.0.0.1';
const PORT_FALLBACK = process.env.HTML_SKILLS_PORT_FALLBACK === '1';
const MAX_BODY_BYTES = 256 * 1024;

// Per-session loopback handshake value (not a credential or external secret).
const TOKEN = process.env.HTML_SKILLS_CHANNEL_TOKEN || crypto.randomBytes(16).toString('hex');

// Constant-time comparison (length-gated; timingSafeEqual needs equal sizes).
function tokenMatches(presented) {
  if (typeof presented !== 'string') return false;
  const a = Buffer.from(presented);
  const b = Buffer.from(TOKEN);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

function log(s) {
  // stderr for diagnostics; stdout carries only submission lines.
  process.stderr.write(`[html-skills-channel] ${s}\n`);
}

function notify(method, params) {
  process.stdout.write(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n');
}

// '*' is safe: responses carry nothing beyond { ok }, forwarding is gated on the
// handshake value above, and reflecting Origin would break file:// artifacts
// (Origin: null) for no security gain.
const CORS = { 'Access-Control-Allow-Origin': '*' };

function reply(res, status, body) {
  if (res.headersSent) return;
  res.writeHead(status, { 'Content-Type': 'application/json', ...CORS });
  res.end(JSON.stringify(body));
}

async function handle(req, res) {
  // Preflight carries no body and no handshake; the POST itself is what's gated.
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      ...CORS,
      'Access-Control-Allow-Headers': 'Content-Type, X-HTML-Skills-Token',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
    });
    res.end();
    return;
  }

  if (req.method !== 'POST') {
    res.writeHead(405, { 'Content-Type': 'text/plain' });
    res.end('html-skills channel: POST a JSON body to deliver into Claude\n');
    return;
  }

  // Cheap DNS-rebinding hardening; the handshake check below is the real gate.
  const hostName = (req.headers.host || '').replace(/:\d+$/, '');
  if (hostName !== '127.0.0.1' && hostName !== 'localhost') {
    reply(res, 403, { ok: false, error: 'bad host' });
    return;
  }

  // Validated BEFORE the body is read or forwarded.
  let presented = null;
  try {
    presented = new URL(req.url, 'http://127.0.0.1').searchParams.get('t');
  } catch (e) {
    /* malformed URL; fall through to the header */
  }
  if (!presented) presented = req.headers['x-html-skills-token'] || null;
  if (!tokenMatches(presented)) {
    reply(res, 403, { ok: false, error: 'missing or invalid channel token' });
    return;
  }

  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) {
      reply(res, 413, { ok: false, error: 'body too large' });
      return;
    }
    chunks.push(chunk);
  }
  const body = Buffer.concat(chunks).toString('utf8');

  // Routing attributes for the notification, best-effort: a handshake-validated
  // submission with a non-JSON body is still forwarded with empty meta.
  const meta = {};
  try {
    const parsed = JSON.parse(body);
    if (parsed && typeof parsed === 'object') {
      if (typeof parsed.skill === 'string') meta.skill = parsed.skill;
      if (typeof parsed.kind === 'string') meta.kind = parsed.kind;
      if (typeof parsed.version === 'number') meta.version = String(parsed.version);
    }
  } catch (e) {
    /* leave meta empty; forward raw body */
  }

  notify('notifications/claude/channel', { content: body, meta });
  reply(res, 200, { ok: true });
}

const httpServer = http.createServer((req, res) => {
  req.on('error', err => log(`request aborted: ${err.code || err.message}`));
  handle(req, res).catch(err => {
    log(`request failed: ${err.code || err.message}`);
    try {
      reply(res, 400, { ok: false, error: 'request failed' });
    } catch (e) {
      /* socket already gone */
    }
  });
});

let fellBack = false;
httpServer.on('error', err => {
  if (err.code === 'EADDRINUSE' && PORT !== 0 && PORT_FALLBACK && !fellBack) {
    fellBack = true;
    log(`port ${PORT} is busy; falling back to an ephemeral port`);
    setImmediate(() => httpServer.listen(0, HOST));
    return;
  }
  if (err.code === 'EADDRINUSE') {
    log(`port ${PORT} is already in use — set HTML_SKILLS_CHANNEL_PORT to an open port (or leave it unset for an ephemeral one)`);
  } else {
    log(`http error: ${err.message}`);
  }
  process.exit(1);
});

httpServer.on('listening', () => {
  // The handshake rides in the URL so it reaches `window.__CLAUDE_SUBMIT_URL__`
  // intact; listen.sh captures this whole line.
  const actualPort = httpServer.address().port;
  log(`listening on http://${HOST}:${actualPort}/?t=${TOKEN}`);
});

httpServer.listen(PORT, HOST);

process.on('unhandledRejection', err => log(`unhandled rejection: ${(err && err.stack) || err}`));
process.on('uncaughtException', err => log(`uncaught exception: ${(err && err.stack) || err}`));
process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));
