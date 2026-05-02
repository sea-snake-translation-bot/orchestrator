#!/usr/bin/env bash
# Lists bot PRs (open + recently merged) with activity in the last N minutes.
# Usage: ./scripts/check-feedback.sh [minutes]   (default: 20)
# Requires: GH_TOKEN in the environment.
set -euo pipefail
cd "$(dirname "$0")/.."

config=$(python3 -c "
import yaml, json, sys
with open('repos.yml') as f:
    print(json.dumps(yaml.safe_load(f)))
")

bot_user=$(echo "$config" | jq -r '.bot_user')
bot_org=$(echo "$config" | jq -r '.bot_org')
minutes="${1:-20}"

# Date N minutes ago (macOS + Linux compatible)
since=$(date -u -d "${minutes} minutes ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
  || date -u -v-"${minutes}"M +%Y-%m-%dT%H:%M:%SZ)

cutoff_14d=$(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
  || date -u -v-14d +%Y-%m-%dT%H:%M:%SZ)

result="[]"

# Use process substitution to avoid subshell from pipe
while IFS= read -r repo; do
  name=$(echo "$repo" | cut -d/ -f2)
  fork="${bot_org}/${name}"

  # Open PRs authored by the bot, updated recently
  open=$(gh pr list --repo "$repo" --state open --author "$bot_user" \
    --json number,title,headRefName,updatedAt \
    --jq "[.[] | select(.updatedAt >= \"$since\")]" 2>/dev/null || echo "[]")

  open=$(echo "$open" | jq \
    --arg r "$repo" --arg f "$fork" \
    '[.[] + {repo: $r, fork: $f, merged: false}]')

  # Merged PRs authored by the bot (within 14 days), updated recently
  merged=$(gh pr list --repo "$repo" --state merged --author "$bot_user" --limit 30 \
    --json number,title,headRefName,updatedAt,mergedAt \
    --jq "[.[] | select(.mergedAt >= \"$cutoff_14d\") | select(.updatedAt >= \"$since\")]" 2>/dev/null || echo "[]")

  merged=$(echo "$merged" | jq \
    --arg r "$repo" --arg f "$fork" \
    '[.[] + {repo: $r, fork: $f, merged: true}]')

  result=$(echo "$result" "$open" "$merged" | jq -s 'add')

done < <(echo "$config" | jq -r '.repos[].repo')

echo "$result" | jq .

count=$(echo "$result" | jq 'length')
if [ "$count" -eq 0 ]; then
  echo "No bot PRs with recent activity." >&2
else
  echo "$count PR(s) with activity in the last $minutes minutes." >&2
fi

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "prs=$(echo "$result" | jq -c .)" >> "$GITHUB_OUTPUT"
fi
