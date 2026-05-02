#!/usr/bin/env bash
# Creates forks for every repo in repos.yml that doesn't have one yet.
# Syncing is NOT done here — each workflow syncs before it runs.
# Requires: GH_TOKEN (BOT_PAT) in the environment.
set -euo pipefail
cd "$(dirname "$0")/.."

config=$(python3 -c "
import yaml, json, sys
with open('repos.yml') as f:
    print(json.dumps(yaml.safe_load(f)))
")

bot_org=$(echo "$config" | jq -r '.bot_org')

echo "$config" | jq -r '.repos[].repo' | while read -r repo; do
  name=$(echo "$repo" | cut -d/ -f2)
  fork="${bot_org}/${name}"

  if gh repo view "$fork" --json name &>/dev/null; then
    echo "$repo → $fork (exists)"
  else
    echo "$repo → creating fork..."
    gh repo fork "$repo" --org "$bot_org" --clone=false 2>/dev/null \
      || gh repo fork "$repo" --clone=false  # fallback: fork to personal account
    sleep 5
    echo "$repo → $fork (created)"
  fi
done

echo "Setup complete."
