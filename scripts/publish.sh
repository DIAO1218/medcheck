#!/usr/bin/env bash
# Publish this repository to GitHub, then open the branch protection that D7 asks for.
#
#   ./scripts/publish.sh                 # private repo named medcheck
#   ./scripts/publish.sh medcheck public
#
# Requires: gh installed and logged in (`gh auth login` once).
# Idempotent: re-running only adds the remote if it is missing and pushes.
set -euo pipefail

REPO="${1:-medcheck}"
VISIBILITY="${2:-private}"
GH="${GH_BIN:-gh}"

command -v "$GH" >/dev/null 2>&1 || { echo "gh not found; install GitHub CLI or set GH_BIN" >&2; exit 1; }
"$GH" auth status >/dev/null 2>&1 || { echo "not logged in; run: gh auth login" >&2; exit 1; }

if git remote get-url origin >/dev/null 2>&1; then
  echo "remote origin already exists: $(git remote get-url origin)"
else
  "$GH" repo create "$REPO" "--$VISIBILITY" --source=. --remote=origin \
    --description "MedCheck - medication interaction and dose-ceiling adjudication with a deterministic safety core (CS5351, NOT FOR CLINICAL USE)" \
    --push
fi

git push -u origin main
git push origin s0-baseline 2>/dev/null || echo "note: tag s0-baseline not pushed (already there, or missing)"

"$GH" repo edit --add-topic "agentic-engineering" --add-topic "safety-critical" \
  --add-topic "deterministic-ai" --add-topic "cs5351" >/dev/null 2>&1 || true

echo
echo "opening branch protection (requires a human review and the 'all gates' check)"
if "$GH" api -X PUT "repos/{owner}/$REPO/branches/main/protection" \
  -F required_status_checks.strict=true \
  -F 'required_status_checks.contexts[]=all gates' \
  -F enforce_admins=true \
  -F required_pull_request_reviews.required_approving_review_count=1 \
  -F restrictions=null >/dev/null 2>&1; then
  echo "branch protection: ON (main needs a PR, one approval, and a green 'all gates')"
else
  echo "branch protection: NOT SET"
  echo "  reason: the 'all gates' check has not run yet (or the token lacks admin scope)."
  echo "  fix: wait for the first CI run on GitHub, then re-run this script."
fi

echo
echo "done: $("$GH" repo view --json url -q .url 2>/dev/null || echo "$REPO")"
