---
name: Handoff sources
description: Where the owner's brief, specification, audit notes, logo files and reusable analytics can be read, and the rules for using them.
---

The planning conversation's files (`PROJECT_BRIEF.md`, `MASTER_PROMPT_v1.0.md`,
`AUDIT_NOTES.md`, `brand/`, `smart_trader_analytics/`, `freqtrade_gate_probe/`) live in
`stai_handoff/` at the project root. They were meant to arrive through a merge the owner
approves. On 17 Nov 2026 the merge had not arrived, and the owner chose to have them copied
from the conversation's attachment folder (`.conversation/stai_handoff/`) instead. The copy is
byte-identical to that source.

**Why:** The brief forbids redrawing the logo or rewriting the analytics from scratch, and
says to ask the owner if a needed file is missing. `.conversation/` belongs to the chat, not
to the project, so it cannot be relied on in a later session or in a task's own environment.

**How to apply:**
- Treat `stai_handoff/` as read-only. Port by copying into the application's own folders.
- If the planned merge shows up later, its files should be identical; if they differ, ask the
  owner which version is current rather than choosing.
- If the folder is ever missing, ask the owner. Do not recreate its contents.
- The specification is the governing document; where the brief's owner decisions (A2) differ, they win.
