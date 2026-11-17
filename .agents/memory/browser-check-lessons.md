---
name: Browser check lessons
description: What makes browser checks of STAI report false failures, how the signed-in screens were checked without a real sign-in, and where the uncommitted one-off harnesses are.
---

- The web app cancels a screen's own API calls when the screen is left (React Query on
  unmount). The browser reports each cancelled call as a failed request.
- A complete sign-in cannot be driven by a test, because it goes through Replit's real sign-in
  service. The signed-in screens were checked by starting a second backend against a throwaway
  database, opening a session for a made-up owner with the backend's own session code, and
  routing the web app's API calls to that backend.
- The workspace preview is an embedded page and the browser withholds the sign-in cookies
  there, so a signed-in check has to drive a top-level page.
- Two one-off harnesses did the signed-in check and the production-form check. They are in
  `generated-artifacts/` (`signed-in-check/`, `prod-check/`), which Git ignores. They are not
  part of the test suite and may be absent in another environment.

**Why:** A test that navigates while calls are under way sees request failures that are not
faults. The audit trail is append-only, so a test sign-in written to the development database
could never be removed, and the documents say that nobody has signed in there before the owner
does. The owner was told that only the signed-out browser test is committed and repeatable.

**How to apply:**
- In a browser test, leave a screen only after its API calls have finished. After that, treat
  any failed request as real.
- Never let a check that signs in write to the development database. Use a throwaway one.
- Keep `pnpm run test:browser` outside `pnpm run check`: it needs both workflows running.
- If the harnesses are missing, rebuild from the description above. Do not present their
  earlier results as repeatable.
