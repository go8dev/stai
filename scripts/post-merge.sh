#!/bin/bash
# Runs automatically after a task is merged into the main project, from the project root.
# It brings a workspace in line with the merged code and is safe to run again at any time.
set -euo pipefail

# TypeScript dependencies, exactly as locked.
pnpm install --frozen-lockfile

# Python dependencies, exactly as locked, including the checks-only group.
uv sync --frozen

# Structure of the development database. Migrations refuse to run on a published machine;
# the published database gets its structure from Replit's Publish step.
pnpm run db:migrate
