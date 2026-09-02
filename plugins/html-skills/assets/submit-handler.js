// Universal submit + clipboard handler for HTML skills in this plugin.
//
// Two functions exposed on window:
//
//   submitToClaude(payload, opts) — primary export. Posts the standard
//     payload envelope to the agent. Two delivery modes:
//       1. Server mode    — agent injected window.__CLAUDE_SUBMIT_URL__
//                           before handing the artifact off; submit POSTs
//                           JSON there. Used only when the agent is certain
//                           its localhost is reachable from the user's
//                           browser (local Claude Code).
//       2. Clipboard mode — default. submit copies JSON; user pastes back.
//     If server mode was configured but the POST fails (listener died, port
//     changed, 403), the handler falls back to clipboard AND says so in the
//     toast, so a dead listener is visible instead of silent.
//
//   copyToClipboard(text, opts) — generic clipboard helper. Use this for
//     ANY clipboard write in an artifact (e.g. a "copy CSS" or "copy URL"
//     button). Never call navigator.clipboard.writeText directly — that
//     skips the fallbacks and leaves the user with "can't copy" UX in
//     contexts where the modern API rejects.
//
//   submitToClaude(payload, { redactSecrets: true }) — opt-in, off by
//     default. Strips high-confidence credential patterns (PEM private
//     keys, AKIA…, ghp_/gho_…, xox…-, sk-…, AIza…, eyJ… JWTs,
//     scheme://user:pass@ URLs) from the serialized payload before
//     sending/copying, replacing each with a re-joinable
//     '{{REDACTED:<type>:…<last4>}}' marker and showing a visible notice.
//     Intended for config/env-shaped editors (see html-throwaway-editor's
//     "Secrets are never embedded" rule, which is the primary defense —
//     this is a last net, not the masking step).
//
// Clipboard mode tries the modern Promise API first; if that rejects (file://
// restrictions in Safari, iframe Permissions-Policy, etc.) it falls back to
// the legacy document.execCommand('copy') path which works in many of those
// contexts. Both paths normally hit the clipboard silently. As an absolute
// last resort — both methods failed — a small non-blocking banner pinned to
// the bottom shows the JSON in a pre-selected textarea with a one-line
// "select all, copy, paste back into Claude" instruction. No modal, ever.
//
// Optional message overrides (window globals or opts):
//   __CLAUDE_SERVER_MESSAGE__ / opts.serverMessage       — after a successful POST
//   __CLAUDE_CLIPBOARD_MESSAGE__ / opts.clipboardMessage — plain clipboard mode
//   __CLAUDE_FALLBACK_MESSAGE__ / opts.fallbackMessage   — server mode failed, copied instead
//
// Payload envelope (both modes carry the same JSON; pretty-printed on the
// clipboard, compact on the wire since the receiver relays it into a
// one-line notification):
//   { skill: "html-<name>", kind: "<artifact-kind>", data: <...>, version: 1 }

(function () {
  // Opt-in payload redaction (opts.redactSecrets) — deliberately narrow.
  // This handler is shared by every html-skills artifact, so only
  // high-confidence credential patterns are stripped; fuzzy heuristics
  // (entropy guesses, "token"-ish key names) would corrupt legitimate
  // payloads from other skills (design tokens, hashes, dataset rows).
  // Each match becomes a re-joinable '{{REDACTED:<type>:…<last4>}}' marker
  // the agent can restore from the original source, and a visible notice
  // reports the count — never silent mutation.
  const SECRET_PATTERNS = [
    ['private-key', /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----/g],
    ['aws-key-id', /\bAKIA[0-9A-Z]{16}\b/g],
    ['github-token', /\bgh[opsur]_[A-Za-z0-9]{20,}\b/g],
    ['slack-token', /\bxox[abprse]-[A-Za-z0-9-]{10,}\b/g],
    ['openai-key', /\bsk-[A-Za-z0-9_-]{20,}\b/g],
    ['google-key', /\bAIza[0-9A-Za-z_-]{30,}\b/g],
    ['jwt', /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/g],
    ['url-userinfo', /\b[a-z][a-z0-9+.-]*:\/\/[^\s/:@"']+:[^\s/@"']+@/gi],
  ];

  function redactKnownSecrets(json) {
    let count = 0;
    for (const pair of SECRET_PATTERNS) {
      json = json.replace(pair[1], function (m) {
        count++;
        // url-userinfo matches end inside the password — there is no safe
        // last-4 preview for passwords, so emit a fixed marker instead.
        if (pair[0] === 'url-userinfo') return '{{REDACTED:url-userinfo}}';
        return '{{REDACTED:' + pair[0] + ':…' + m.slice(-4) + '}}';
      });
    }
    return { json: json, count: count };
  }

  function compact(json) {
    try { return JSON.stringify(JSON.parse(json)); } catch (e) { return json; }
  }

  async function submitToClaude(payload, opts) {
    opts = opts || {};
    let json = JSON.stringify(payload, null, 2);
    let note = '';

    if (opts.redactSecrets) {
      const red = redactKnownSecrets(json);
      if (red.count > 0) {
        json = red.json;
        note = ' (' + red.count + ' secret-looking value'
          + (red.count === 1 ? '' : 's') + ' redacted)';
      }
    }

    const url = opts.url || window.__CLAUDE_SUBMIT_URL__;
    let serverFailure = '';

    if (url) {
      try {
        const r = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: compact(json),
        });
        if (r.ok) {
          notify(opts, (opts.serverMessage
            || window.__CLAUDE_SERVER_MESSAGE__
            || 'Submitted to Claude.') + note);
          return 'server';
        }
        serverFailure = 'HTTP ' + r.status;
      } catch (e) {
        serverFailure = 'unreachable';
      }
    }
    return clipboardSubmit(json, opts, note, serverFailure);
  }

  async function clipboardSubmit(json, opts, note, serverFailure) {
    let msg;
    if (serverFailure) {
      msg = opts.fallbackMessage
        || window.__CLAUDE_FALLBACK_MESSAGE__
        || ("Claude's listener didn't answer (" + serverFailure + ") — copied to clipboard instead. Paste it into Claude.");
    } else {
      msg = opts.clipboardMessage
        || window.__CLAUDE_CLIPBOARD_MESSAGE__
        || 'Copied to clipboard — paste back into Claude.';
    }
    return copyToClipboard(json, { ...opts, message: msg + (note || ''), returnTag: 'clipboard' });
  }

  // Standalone clipboard helper, exposed on window. Use this for ANY
  // clipboard write in an artifact — never call navigator.clipboard.writeText
  // directly, since that skips the execCommand fallback and the inline
  // banner, leaving the user stuck with a "can't copy" message in the
  // contexts where the modern API rejects.
  async function copyToClipboard(text, opts) {
    opts = opts || {};
    const msg = opts.message || 'Copied to clipboard.';
    if (await tryAsyncClipboard(text)) {
      notify(opts, msg);
      return opts.returnTag || 'copied';
    }
    if (copyViaExecCommand(text)) {
      notify(opts, msg);
      return opts.returnTag || 'copied';
    }
    showInlineFallback(text);
    return 'manual';
  }

  async function tryAsyncClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      return false;
    }
  }

  function copyViaExecCommand(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    Object.assign(ta.style, {
      position: 'fixed', top: '0', left: '0',
      width: '1px', height: '1px', opacity: '0',
    });
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (e) {}
    ta.remove();
    return ok;
  }

  function notify(opts, msg) {
    if (typeof opts.onResult === 'function') { opts.onResult(msg); return; }
    const el = document.createElement('div');
    el.textContent = msg;
    el.setAttribute('role', 'status');
    Object.assign(el.style, {
      position: 'fixed', bottom: '16px', left: '50%',
      transform: 'translateX(-50%)', background: '#111', color: '#fff',
      padding: '10px 14px', borderRadius: '8px', font: '14px system-ui',
      zIndex: 99999, boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
    });
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3500);
  }

  // Absolute last resort: both clipboard paths failed. Drop a small
  // non-blocking banner pinned to the bottom of the page with the JSON
  // pre-selected and a one-line instruction. NEVER a modal — the rest of
  // the page stays interactive.
  function showInlineFallback(json) {
    const wrap = document.createElement('div');
    wrap.setAttribute('role', 'region');
    wrap.setAttribute('aria-label', 'Manual copy required');
    Object.assign(wrap.style, {
      position: 'fixed', left: '50%', bottom: '12px',
      transform: 'translateX(-50%)',
      width: 'min(720px, calc(100% - 24px))',
      background: '#111', color: '#fff',
      borderRadius: '10px', padding: '10px 12px',
      boxShadow: '0 6px 24px rgba(0,0,0,0.3)',
      zIndex: 99999,
      font: '13px system-ui, -apple-system, sans-serif',
      display: 'grid', gridTemplateColumns: '1fr auto',
      columnGap: '8px', alignItems: 'start',
    });

    const main = document.createElement('div');
    const msg = document.createElement('div');
    const isApple = /Mac|iPhone|iPad|iPod/.test(navigator.platform || navigator.userAgent || '');
    msg.textContent = 'Auto-copy unavailable here. Press '
      + (isApple ? '⌘A then ⌘C' : 'Ctrl+A then Ctrl+C')
      + ' in the box, then paste into Claude.';
    msg.style.marginBottom = '6px';
    main.appendChild(msg);

    const ta = document.createElement('textarea');
    ta.value = json;
    ta.readOnly = true;
    ta.spellcheck = false;
    Object.assign(ta.style, {
      width: '100%', minHeight: '60px', maxHeight: '160px',
      resize: 'vertical', padding: '6px 8px',
      font: '12px ui-monospace, monospace',
      background: '#fff', color: '#111',
      border: 'none', borderRadius: '6px', outline: 'none',
      boxSizing: 'border-box',
    });
    main.appendChild(ta);

    const close = document.createElement('button');
    close.type = 'button';
    close.textContent = '×';
    close.setAttribute('aria-label', 'Dismiss');
    Object.assign(close.style, {
      background: 'transparent', border: 'none', color: '#fff',
      fontSize: '18px', cursor: 'pointer', lineHeight: '1',
      padding: '2px 4px', alignSelf: 'start',
    });
    close.addEventListener('click', () => wrap.remove());

    wrap.append(main, close);
    document.body.appendChild(wrap);

    setTimeout(() => { ta.focus(); ta.select(); }, 0);
  }

  window.submitToClaude = submitToClaude;
  window.copyToClipboard = copyToClipboard;
})();
