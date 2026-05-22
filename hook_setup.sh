#!/bin/bash
# Install all Quantum Metal git hooks by symlinking from ``hooks/`` into
# ``.git/hooks/``. Idempotent — re-running just refreshes the symlinks.
#
# Hooks installed:
#   - pre-commit: ruff check + format-check on staged Python files
#                 (matches CI ``lint`` / ``format`` jobs)
#   - pre-push:   full-repo ruff + env-consistency + tutorials-sync
#                 (matches CI ``lint``, ``format``, ``env.yml drift``,
#                 ``tutorials sync`` jobs)
#
# Run from the repo root: ``./hook_setup.sh``
#
# On Windows: run from Git Bash or another POSIX shell.

set -e

# Resolve repo root from the script location so it works regardless of CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d .git ]]; then
    echo "Error: .git directory not found. Run from the repo root, or after git init/clone."
    exit 1
fi

mkdir -p .git/hooks

failed=0
for hook in pre-commit pre-push; do
    if [[ ! -f "hooks/$hook" ]]; then
        echo "Warning: hooks/$hook missing in repo; skipping"
        continue
    fi
    if ln -s -f "../../hooks/$hook" ".git/hooks/$hook"; then
        chmod +x "hooks/$hook"   # ensure the source script itself is executable
        echo "  ✓ installed $hook"
    else
        echo "  ✗ failed to install $hook"
        failed=1
    fi
done

if [[ $failed -ne 0 ]]; then
    echo "Linking hooks failed."
    exit 1
fi

echo "Hook setup complete. Test with: bash hooks/pre-commit  (or commit something)."
