---
name: Publishing is the owner's step
description: Which publish-related tools to hold back until the owner has published once, and why.
---

Until the owner has made the first publish, do not show the publish suggestion card, do not
start a publish, and do not call the schema-difference explainer.

**Why:** The region is fixed for good at the first publish. Only the owner can choose it, along
with private access and the machine size, in the Publishing tool's advanced settings. A
one-click publish could go out with the defaults, which are North America and public. The
schema-difference explainer sets up a production read replica the first time it is used, which
creates something in production before the owner has decided to publish.

**How to apply:**
- Describe the path in words and point to the publish checklist in `README.md`.
- The checks on the live app are done together with the owner, in the checklist's order. If
  the first sign-in shows an account ID other than the workspace owner's, stop and ask.
- Comparing the production structure with development needs the owner's go-ahead first. The
  checklist says so.
- Once the first publish is done the region is settled. Later publishes still wait for the
  owner: the plan says to publish only while no position is open.
