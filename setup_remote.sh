#!/usr/bin/env bash
# setup_remote.sh
# Configures git remotes for the Portfolio-Linker repository migration.
#
# Usage:
#   bash setup_remote.sh
#
# Prerequisites:
#   - Create the target repository at https://github.com/KPeethi/Portfolio-Linker
#     before running this script.

set -euo pipefail

TARGET_REMOTE="https://github.com/KPeethi/Portfolio-Linker.git"

# Remove the legacy backup remote if it still exists
if git remote | grep -q "^gitsafe-backup$"; then
    git remote remove gitsafe-backup
    echo "Removed remote: gitsafe-backup"
fi

# Point origin at the Portfolio-Linker repository
if git remote | grep -q "^origin$"; then
    git remote set-url origin "$TARGET_REMOTE"
    echo "Updated remote 'origin' to $TARGET_REMOTE"
else
    git remote add origin "$TARGET_REMOTE"
    echo "Added remote 'origin' pointing to $TARGET_REMOTE"
fi

# Push the main branch and set it as the upstream
if ! git push -u origin main; then
    echo "ERROR: Push failed." >&2
    echo "Ensure the repository exists at $TARGET_REMOTE and that you" >&2
    echo "have push access before running this script." >&2
    exit 1
fi
echo "Pushed main branch to origin."
