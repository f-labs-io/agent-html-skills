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
//
//   copyToClipboard(text, opts) — generic clipboard helper. Use this for
//     ANY clipboard write in an artifact (e.g. a "copy CSS" or "copy URL"
//     button). Never call navigator.clipboard.writeText directly — that
//     skips the fallbacks and leaves the user with "can't copy" UX in
//     contexts where the modern API rejects.
//
// Clipboard mode tries the modern Promise API first; if that rejects (file://
// restrictions in Safari, iframe Permissions-Policy, etc.) it falls back to
// the legacy document.execCommand('copy') path which works in many of those
// contexts. Both paths normally hit the clipboard silently. As an absolute
// last resort — both methods failed — a small non-blocking banner pinned to
// the bottom shows the JSON in a pre-selected textarea with a one-line
// "Cmd+A, Cmd+C, paste back into Claude" instruction. No modal, ever.
//
// Payload envelope (both modes carry the same JSON):
//   { skill: "html-<name>", kind: "<artifact-kind>", data: <...>, version: 1 }

(function () {
  async function submitToClaude(payload, opts) {
    opts = opts || {};
    const json = JSON.stringify(payload, null, 2);
    const url = opts.url || window.__CLAUDE_SUBMIT_URL__;

    if (url) {
      try {
        const r = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: json,
        });
        if (r.ok) {
          notify(opts, opts.serverMessage
            || window.__CLAUDE_SERVER_MESSAGE__
            || 'Submitted to Claude.');
          return 'server';
        }
      } catch (e) {
        // Fall through to clipboard.
      }
    }
    return clipboardSubmit(json, opts);
  }

  async function clipboardSubmit(json, opts) {
    const msg = opts.clipboardMessage
      || window.__CLAUDE_CLIPBOARD_MESSAGE__
      || 'Copied to clipboard — paste back into Claude.';
    return copyToClipboard(json, { ...opts, message: msg, returnTag: 'clipboard' });
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
    msg.textContent = 'Auto-copy unavailable here. Press ⌘A then ⌘C in the box, then paste into Claude.';
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
