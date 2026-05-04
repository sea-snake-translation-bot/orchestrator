#!/usr/bin/env bash
# Lists bot PRs that may have unaddressed feedback:
#   - ALL open bot PRs (no time filter — Claude checks each one for unaddressed comments)
#   - Merged bot PRs within the last 14 days (time-bounded to avoid ancient history)
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

cutoff_14d=$(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
  || date -u -v-14d +%Y-%m-%dT%H:%M:%SZ)

result="[]"

while IFS= read -r repo; do
  name=$(echo "$repo" | cut -d/ -f2)
  fork="${bot_org}/${name}"

  # ALL open PRs from the bot — no time filter, Claude decides what's unaddressed
  open=$(gh pr list --repo "$repo" --state open --author "$bot_user" \
    --json number,title,headRefName,updatedAt \
    --jq '[.[] | . + {merged: false}]' 2>/dev/null || echo "[]")

  open=$(echo "$open" | jq \
    --arg r "$repo" --arg f "$fork" \
    '[.[] + {repo: $r, fork: $f}]')

  # Merged PRs within 14 days — feedback can still land after merge
  merged=$(gh pr list --repo "$repo" --state merged --author "$bot_user" --limit 30 \
    --json number,title,headRefName,updatedAt,mergedAt \
    --jq "[.[] | select(.mergedAt >= \"$cutoff_14d\")]" 2>/dev/null || echo "[]")

  merged=$(echo "$merged" | jq \
    --arg r "$repo" --arg f "$fork" \
    '[.[] + {repo: $r, fork: $f, merged: true}]')

  result=$(echo "$result" "$open" "$merged" | jq -s 'add')

done < <(echo "$config" | jq -r '.repos[].repo')

echo "$result" | jq .

count=$(echo "$result" | jq 'length')
if [ "$count" -eq 0 ]; then
  echo "No bot PRs found." >&2
else
  echo "$count bot PR(s) queued for feedback check." >&2
fi

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "prs=$(echo "$result" | jq -c .)" >> "$GITHUB_OUTPUT"
fi
