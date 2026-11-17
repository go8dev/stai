---
name: No Git repository in the workspace
description: The workspace has no .git directory; what that means for the specification's Git workflow requirement.
---

`git` is installed, but the project folder is not a Git repository (checked 17 Nov 2026), and
initialising one by hand is off limits on this platform.

**Why:** The specification (section 11.3) asks for Git from the beginning, readable commits and
feature branches. Promising those without a repository would be untrue.

**How to apply:**
- Never run `git init`, rewrite history or force-push.
- Version history comes from the platform's checkpoints, and each phase is delivered as a task
  that the owner accepts before it joins the main project.
- Per Replit's documentation a project has no repository until the owner chooses "Initialize
  Git Repository" in the Git pane; after that, checkpoints appear as commits. That step is the
  owner's. Check again for `.git` before saying anything about commits.
- Keep `.gitignore` and `.replitignore` correct regardless, and never write secrets to files.
