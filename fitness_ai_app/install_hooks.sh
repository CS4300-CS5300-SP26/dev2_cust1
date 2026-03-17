#!/usr/bin/env bash
# install_hooks.sh – copies the project's git hook templates into .git/hooks/
#
# Run once after cloning the repository:
#   bash fitness_ai_app/install_hooks.sh

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SOURCE_DIR="$REPO_ROOT/fitness_ai_app/hooks"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

for hook in "$SOURCE_DIR"/*; do
    name="$(basename "$hook")"
    dest="$HOOKS_DIR/$name"
    cp "$hook" "$dest"
    chmod +x "$dest"
    echo "✅ Installed $name → $dest"
done

echo ""
echo "Git hooks installed. To skip tests for a single commit, use:"
echo "  SKIP_TESTS=1 git commit -m \"your message\""
