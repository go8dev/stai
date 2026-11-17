---
name: Git in the workspace
description: How this project came to have a Git repository, and what that means for the specification's Git workflow requirement.
---

The project folder had no Git repository when the plan was written. One appeared on
17 Nov 2026, between two turns, without `git init` being run from the shell. Its first commits
carry the platform's agent identity. Whether the owner pressed "Initialize Git Repository" or
the platform created it with the first checkpoint was not determined, so do not tell the owner
which it was.

**Why:** The specification (section 11.3) asks for Git from the beginning, readable commits and
feature branches. Anything said about commits, branches or remotes has to match what exists.

**How to apply:**
- Never run `git init`, rewrite history or force-push. Read-only git commands are fine; use
  `GIT_OPTIONAL_LOCKS=0` so a status check does not take the index lock.
- Checkpoints appear as commits. Each phase is delivered as a task that the owner accepts
  before it joins the main project, which is how the feature-branch requirement is met.
- A platform backup remote is not a GitHub connection. Connecting GitHub is the owner's step;
  check `git remote -v` before saying anything about a remote.
- Files the platform writes for you can be tracked. See the note on personal values and Secrets.
