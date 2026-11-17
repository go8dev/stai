---
name: Workspace runtime quirks
description: Platform behaviour in this workspace that affects running a second backend, restart checks, the runtime-only dependency set and dates in documents.
---

- A platform process answers on port 18080 and forwards to the API workflow's port 8080. A
  request sent there reaches the development backend and the development database.
- After the platform restores the workflows, a second copy of the backend is sometimes started.
  It finds the port taken, says so and exits. The first copy keeps serving.
- Uvicorn re-raises SIGTERM after a graceful shutdown, so a cleanly stopped backend exits with
  status -15, not 0.
- `uv sync --no-dev` removes the check tools (pytest, Ruff) from the environment it targets.
- The container clock is UTC. The owner's day is Asia/Manila, eight hours ahead.

**Why:** Each of these led to a wrong conclusion or a broken environment once: a check that
seemed to talk to a throwaway backend, a "port in use" line read as a crash, a clean stop read
as a failure, a workspace left without pytest.

**How to apply:**
- For a second backend, ask the operating system for a free port. Never pick a fixed number,
  and confirm which process owns a port before trusting an answer from it.
- Before restarting a workflow over a "port in use" line, check whether the backend is already
  serving.
- In a stop or restart check, accept exit status 0 or -15 and look for the shutdown log line.
- To reproduce the published dependency set, build it into a separate environment outside the
  project (`UV_PROJECT_ENVIRONMENT` pointing under `/tmp`), never into the workspace one.
- Date entries in project documents by the owner's day, not the container's.
