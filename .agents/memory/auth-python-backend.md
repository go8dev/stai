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

**How to apply:** This is a proposal (item 17) until the owner approves it. If the owner
prefers otherwise, the alternatives are Clerk with a small Node gateway or a self-built
email and password login. The platform's Replit Auth instructions are written for Express;
reuse their flow and security rules, not their code.
