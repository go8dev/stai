---
name: Auth choice for a Python backend
description: Why STAI proposes Replit sign-in instead of the platform's default Clerk setup.
---

Replit-managed Clerk depends on a proxy middleware that runs inside the Express server in
production (required even for apps with no backend). With a FastAPI backend that would mean
keeping a Node process in front of Python only for sign-in.

Replit sign-in is plain OpenID Connect with PKCE, works on published domains regardless of
backend language, and can be implemented in Python directly. Access is restricted to the
owner's Replit user ID.

**Why:** The specification wants one custom backend and the simplest reliable solution; the
owner is the only user.

**How to apply:** The owner approved this on 17 Nov 2026 (item 17) and Phase 1 built it. The
platform's Replit Auth instructions are written for Express: keep their flow, route names,
browser-side package and security rules, and write only the server side in Python. The tests
use a stand-in for Replit's sign-in service, so the owner's first sign-in is the first real
one. If it shows an account ID other than the workspace owner's, stop and ask the owner.
