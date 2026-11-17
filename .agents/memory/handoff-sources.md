---
name: Handoff sources
description: Where the owner's brief, specification, audit notes, logo files and reusable analytics can be read, and the rules for using them.
---

The planning conversation's files (`PROJECT_BRIEF.md`, `MASTER_PROMPT_v1.0.md`,
`AUDIT_NOTES.md`, `brand/`, `smart_trader_analytics/`, `freqtrade_gate_probe/`) are meant to
arrive as `stai_handoff/` at the project root through a merge the owner approves. On
17 Nov 2026 that folder had not arrived, but the same files were readable under
`.conversation/stai_handoff/`.

**Why:** The brief says to ask the owner if a needed file is missing, and forbids redrawing
the logo or rewriting the analytics from scratch. `.conversation/` belongs to the chat, not
to the project, so it may not exist in a later session.

**How to apply:**
- Check the project root first, then `.conversation/stai_handoff/`. If neither exists, ask the owner.
- Treat both locations as read-only. Port by copying into the application's own folders.
- Copy from `.conversation/` only after the owner has said to; otherwise wait for the merge.
- The specification is the governing document; where the brief's owner decisions (A2) differ, they win.
