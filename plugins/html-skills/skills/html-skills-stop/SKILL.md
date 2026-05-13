---
name: html-skills-stop
description: >-
  Tears down server mode for html-skills for THIS Claude Code session — kills the receiver, stops the `Monitor` armed by `html-skills-listen`, and cleans up its temp files. Parallel sessions are unaffected. Invoke when the user is done with interactive html-skills artifacts ("I'm done with html-skills", "stop the listener", "end html-skills session"), OR at session end if the user mentions cleanup. Safe to invoke when nothing is active — it reports inactive and exits.
license: MIT
---

# html-skills-stop — tear down server mode

Pairs with `html-skills-listen`. Runs a bundled bash script that kills this session's receiver and removes its temp files, then stops the `Monitor` task whose ID was saved by `html-skills-listen`.

## Steps

1. **Run the teardown script:**

   ```bash
   bash scripts/stop.sh
   ```

   Output: `KEY=VALUE` lines. Always: `SID`, `STATUS`. When a Monitor was armed by `html-skills-listen` and saved, also: `MONITOR_ID`.

2. **If `MONITOR_ID` is printed, stop the Monitor task:**

   Call `TaskStop(task_id: "<MONITOR_ID>")`. If it fails because the task is already gone, that's fine — continue.

3. **Branch on `STATUS`:**

   - **`STATUS=WEB`** — Tell the user: `✓ html-skills server was inactive (web mode).`
   - **`STATUS=INACTIVE`** — Tell the user: `✓ html-skills server was already inactive — nothing to stop.`
   - **`STATUS=STOPPED`** — Tell the user: `✓ html-skills server stopped for this session.`
