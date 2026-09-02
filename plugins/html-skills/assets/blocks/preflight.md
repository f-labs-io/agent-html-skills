## Pre-flight — run BEFORE writing the artifact

Invoke `html-skills:html-skills-listen` (Skill tool) first; it is idempotent. If it returns a URL, inject it verbatim as `window.__CLAUDE_SUBMIT_URL__` in the HTML you are about to write, `?t=` query string included (a local, single-session loopback handshake — not a credential). If it reported web/sandbox mode, leave that line out; `submitToClaude` then falls back to clipboard mode.
