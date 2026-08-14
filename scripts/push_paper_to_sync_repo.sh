#!/usr/bin/env bash
# Push the current paper into ihelfrich/nmtc-paper, the repository that
# Overleaf synchronizes with. Run after regenerating tables or figures.
#
#   bash scripts/push_paper_to_sync_repo.sh ["commit message"]
#
# Overleaf's GitHub synchronization is a premium feature. Without it, the
# repo is still useful: clone it, edit locally, and push.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MSG="${1:-update paper from research repo}"
WORK="${TMPDIR:-/tmp}/nmtc-paper-sync"

cd "$ROOT"
bash scripts/make_overleaf_bundle.sh >/dev/null

rm -rf "$WORK"
git clone -q https://github.com/ihelfrich/nmtc-paper.git "$WORK"
# replace tracked content, preserving git metadata and the ignore file
find "$WORK" -mindepth 1 -maxdepth 1 ! -name .git ! -name .gitignore -exec rm -rf {} +
cp -R "$ROOT/overleaf/." "$WORK/"
rm -f "$WORK/overleaf-nmtc-paper.zip"

cd "$WORK"
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  echo "sync repo already current; nothing to push"
  exit 0
fi
git add -A
git commit -q -m "$MSG"
git push -q origin main
echo "pushed to https://github.com/ihelfrich/nmtc-paper"
