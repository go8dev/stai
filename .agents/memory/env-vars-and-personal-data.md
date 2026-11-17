---
name: Personal values belong in Secrets
description: Where the platform stores plain environment variables, and why the owner's alert address and similar values must be Secrets.
---

Plain environment variables set through the platform's environment tooling are written in
clear text into `.replit`, and `.replit` is tracked by Git. Secrets are stored outside the
project files.

**Why:** On 17 Nov 2026 the owner's alert address was first saved as a shared environment
variable and showed up in `.replit`. It was removed before any commit captured it and
requested as a Secret instead. The project's rule is that personal data and secrets never
appear in a file, log or test, and the owner was told the address is in no project file.

**How to apply:**
- Anything personal goes in Secrets through the secure form, even when it is not a credential.
  Only the owner can enter a Secret; it cannot be set on their behalf.
- Use plain environment variables only for values that are fine to publish with the code.
- After setting any variable, check `.replit` and the Git status before the turn ends.
- The alert address is the Secret `STAI_ALERT_EMAIL`, first used in Phase 4. If it is missing
  when Phase 4 starts, ask the owner to enter it in the secure form; do not copy it from the chat.
