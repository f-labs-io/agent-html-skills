#!/usr/bin/env node
/**
 * html-skills submit receiver.
 *
 * Purpose-built for receiving submissions from interactive HTML artifacts
 * produced by the html-skills plugin. Started in the background by the
 * `html-skills-listen` skill (which lives alongside this file).
 *
 * Architecture:
 *   - Runs a localhost HTTP server on an ephemeral port (set
 *     HTML_SKILLS_CHANNEL_PORT to pin one). Every POST body is emitted
 *     as a single JSON-RPC-shaped notification line on stdout. The
 *     intended consumer is `Monitor`, armed by `html-skills-listen` — it
 *     tails this stdout, filters for
 *     `"method":"notifications/claude/channel"`, and turns each
 *     submission into a session notification for the agent.
 *
 * Also implements the minimum MCP stdio handshake so the process can be
 * spawned as an MCP server without erroring. We do not rely on this path
 * for the submit flow.
 *
 * Zero runtime dependencies.
 */

'use strict';

const http = require('node:http');

// Default to an ephemeral port (0) so parallel Claude Code sessions don't
// collide on the same port. `html-skills-listen` parses the chosen port out
// of the log line below. Set HTML_SKILLS_CHANNEL_PORT to pin a specific port.
const PORT = parseInt(process.env.HTML_SKILLS_CHANNEL_PORT || '0', 10);
const HOST = '127.0.0.1';
const SERVER_NAME = 'html-skills';
const SERVER_VERSION = '0.1.0';
const PROTOCOL_VERSION = '2024-11-05';

const INSTRUCTIONS = [
  'Events from this channel arrive as <channel source="html-skills" ...>.',
  'They are submissions from interactive HTML artifacts produced by the',
  'html-skills plugin (mind maps, kanban boards, mind maps, brainstorm grids,',
  'comparison matrices, parameter playgrounds, design prototype tuners).',
  'The body is JSON with shape: { "skill": "html-<name>", "kind": "<artifact-kind>",',
  '"data": <skill-specific>, "version": 1 }. The `data` field is the actual',
  'user submission — use it to continue whatever task produced the artifact.',
  'No reply tool is exposed; this channel is one-way.',
].join(' ');

// ---------- MCP wire protocol over stdio --------------------------------

let stdinBuf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  stdinBuf += chunk;
  // Messages are delimited by newline (LSP-style framing isn't required
  // for stdio MCP; one JSON object per line is the convention).
  let nl;
  while ((nl = stdinBuf.indexOf('\n')) !== -1) {
    const line = stdinBuf.slice(0, nl).trim();
    stdinBuf = stdinBuf.slice(nl + 1);
    if (line) handleMessage(line);
  }
});
// Don't exit on stdin EOF: real MCP shutdowns happen via SIGTERM/SIGKILL
// from Claude Code, and treating stdin-close as a shutdown signal makes the
// server unusable in plain-Bash background mode (where stdin is /dev/null).

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

function reply(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function replyError(id, code, message, data) {
  send({ jsonrpc: '2.0', id, error: { code, message, ...(data ? { data } : {}) } });
}

function notify(method, params) {
  send({ jsonrpc: '2.0', method, params });
}

function handleMessage(line) {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch (e) {
    log('parse error: ' + e.message);
    return;
  }

  if (msg.method === 'initialize') {
    reply(msg.id, {
      protocolVersion: PROTOCOL_VERSION,
      serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
      capabilities: {
        // Legacy capability declaration; harmless to keep, no longer load-bearing
        // for our submit flow (we deliver via stdout + Monitor, not via MCP).
        experimental: { 'claude/channel': {} },
      },
      instructions: INSTRUCTIONS,
    });
    return;
  }

  if (msg.method === 'initialized' || msg.method === 'notifications/initialized') {
    return; // no-op, just an ack from the client
  }

  if (msg.method === 'ping') {
    reply(msg.id, {});
    return;
  }

  if (msg.method === 'shutdown') {
    reply(msg.id, null);
    setTimeout(() => process.exit(0), 50);
    return;
  }

  if (msg.method === 'tools/list') {
    // We expose no tools (one-way channel).
    reply(msg.id, { tools: [] });
    return;
  }

  if (msg.method === 'resources/list' || msg.method === 'prompts/list') {
    reply(msg.id, msg.method === 'resources/list' ? { resources: [] } : { prompts: [] });
    return;
  }

  // Unknown request: respond with method-not-found if it has an id.
  if (msg.id !== undefined) {
    replyError(msg.id, -32601, `method not found: ${msg.method}`);
  }
}

function log(s) {
  // stderr only — stdout is reserved for MCP traffic.
  process.stderr.write(`[html-skills-channel] ${s}\n`);
}

// ---------- HTTP listener for artifact submissions ----------------------

const httpServer = http.createServer(async (req, res) => {
  // CORS preflight: artifacts opened via file:// or http://localhost on a
  // different port count as a different origin.
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type',
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

  let body = '';
  req.setEncoding('utf8');
  for await (const chunk of req) body += chunk;

  // Pull a few attributes off the payload for the <channel> tag, so Claude
  // can route without parsing the body. Best-effort — non-JSON bodies still
  // get forwarded.
  let meta = {};
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

  // Per the channels-reference, meta keys must be identifiers (letters,
  // digits, underscores). Drop anything that doesn't qualify.
  for (const k of Object.keys(meta)) {
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(k)) delete meta[k];
  }

  notify('notifications/claude/channel', { content: body, meta });

  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  });
  res.end(JSON.stringify({ ok: true }));
});

httpServer.on('error', err => {
  if (err.code === 'EADDRINUSE') {
    log(`port ${PORT} is already in use — set HTML_SKILLS_CHANNEL_PORT to an open port (or leave it unset to grab an ephemeral one)`);
  } else {
    log(`http error: ${err.message}`);
  }
  // Keep the MCP side running anyway; submissions just won't reach us.
});

httpServer.listen(PORT, HOST, () => {
  // Use the actual bound port (PORT may be 0 = ephemeral).
  const actualPort = httpServer.address().port;
  log(`listening on http://${HOST}:${actualPort}/`);
});

process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));
