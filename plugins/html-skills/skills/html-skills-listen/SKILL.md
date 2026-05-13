---
name: html-skills-listen
description: >-
  Sets up the per-session local receiver and `Monitor` for interactive html-skills artifacts so user submissions arrive as session notifications instead of as copy-paste round-trips. Other html-skills interactive skills (html-mind-map, html-throwaway-editor, html-brainstorm-grid, html-comparison-matrix, html-interactive-playground, html-design-prototypes) invoke this skill from their pre-flight block, BEFORE writing the HTML artifact. Idempotent — safe to invoke every time. Returns a localhost URL the parent skill injects as `window.__CLAUDE_SUBMIT_URL__` in the artifact. Don't invoke unprompted in unrelated conversations — this only fires when an interactive html-skills artifact is about to be produced.
license: MIT
---

# html-skills-listen — server-mode setup for interactive artifacts

This skill is a system primitive for the html-skills plugin's interactive artifacts. It runs a bundled bash script that handles environment detection, idempotency, ephemeral-port startup, log parsing, and stale-session cleanup. After the script returns, you arm a `Monitor` on the receiver's stdout so each submit becomes a session notification, and return the URL to the parent skill.

## Steps

1. **Run the setup script:**

   ```bash
   bash scripts/listen.sh
   ```

   The script is self-locating (resolves `server.js` next to itself via `BASH_SOURCE`), so it doesn't depend on `$CLAUDE_PLUGIN_ROOT` being set in your bash environment.

   Output is `KEY=VALUE` lines on stdout. Always present: `SID`, `LOG`, `MIDF`, `STATUS`. When `STATUS=STARTED` or `STATUS=ALREADY_RUNNING` you also get `URL`. Capture `LOG`, `MIDF`, `URL`.

2. **Branch on `STATUS`:**

   - **`STATUS=WEB`** — Claude Code web session. The sandbox can't reach the user's browser. Don't arm `Monitor`. Tell the parent skill (or the user, if invoked directly):

     > ⓘ Claude Code web session detected. Server mode can't work here. The interactive artifact will use clipboard mode automatically — submit copies JSON to clipboard for paste-back.

     Stop here.

   - **`STATUS=ERROR`** — Dump the script output as the error and stop.

   - **`STATUS=ALREADY_RUNNING`** — A `Monitor` was armed in the call that originally started this session's receiver, so don't arm a new one. Return `URL` to the parent skill and stop.

   - **`STATUS=STARTED`** — Continue to step 3.

3. **Arm a persistent `Monitor`** on the receiver's log. Substitute the literal `LOG` value into the `command:` string (the `Monitor` tool can't expand env vars itself):

   ```
   Monitor(
     description: "html-skills artifact submissions",
     command: "tail -f <LOG> | grep --line-buffered '\"method\":\"notifications/claude/channel\"'",
     persistent: true
   )
   ```

   Capture the returned task ID.

4. **Save the Monitor task ID** so `html-skills-stop` can find it later:

   ```bash
   echo "<the-task-id-from-step-3>" > "<MIDF>"
   ```

5. **Return the URL to the parent skill** so it can inject `window.__CLAUDE_SUBMIT_URL__ = '<URL>'` into the HTML artifact. If invoked directly by a user, tell them:

   > ✓ html-skills server active for this session at `<URL>`. I'll be notified the moment any interactive artifact's Submit button is clicked. Invoke `html-skills-stop` when done.

## When invoked directly

A user can ask "set up html-skills listening" or similar. The flow is identical — produce a status message at the end. They don't need to do anything else; the next time an interactive html-skills artifact is generated, it will pick up the URL automatically.
