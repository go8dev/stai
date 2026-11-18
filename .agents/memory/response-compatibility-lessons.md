---
name: Response compatibility lessons
description: Why saved-result extensions need contract generation and legacy-read checks, not runtime checks alone.
---

When extending responses backed by saved research, verify both legacy payload reads and the generated client contract before UI verification.

**Why:** Defaulted additive fields worked at runtime but initially became optional in the wire contract. Switching only selected models into another schema mode then produced unresolved nested references during generation. Runtime success alone did not establish compatibility.

**How to apply:** Keep response completeness, backward-read defaults and the project's combined schema convention consistent. Check generated references and legacy strategy/version assumptions together; do not solve a schema issue by rewriting old saved results.

For bounded historical AI evidence, exercise populated multi-market runs as well as empty runs, and check that trimming retains useful trade evidence rather than merely satisfying the size limit.

**Why:** Empty research results can pass both the endpoint and budget checks while hiding failures that occur only when orders, trades and contextual history coexist.

**How to apply:** Treat both evidence usefulness and total serialized size as completion criteria whenever historical review sampling changes.
