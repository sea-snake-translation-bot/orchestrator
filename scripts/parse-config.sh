#!/usr/bin/env bash
# Reads repos.yml and outputs a JSON array suitable for a GitHub Actions matrix.
# Usage: ./scripts/parse-config.sh [repo-filter]
#   repo-filter  optional owner/name — if set, only that repo is emitted.
# Outputs are also written to $GITHUB_OUTPUT when running inside Actions.
set -euo pipefail
cd "$(dirname "$0")/.."

config=$(python3 -c "
import yaml, json, sys
with open('repos.yml') as f:
    print(json.dumps(yaml.safe_load(f)))
")

bot_org=$(echo "$config" | jq -r '.bot_org')
bot_user=$(echo "$config" | jq -r '.bot_user')
bot_email=$(echo "$config" | jq -r '.bot_email')
filter="${1:-}"

if [ -n "$filter" ]; then
  repos=$(echo "$config" | jq --arg f "$filter" '[.repos[] | select(.repo == $f)]')
else
  repos=$(echo "$config" | jq '.repos')
fi

count=$(echo "$repos" | jq 'length')
if [ "$count" -eq 0 ]; then
  echo "No repos matched${filter:+ filter '$filter'}." >&2
  echo "[]"
  [ -n "${GITHUB_OUTPUT:-}" ] && echo "repos=[]" >> "$GITHUB_OUTPUT"
  exit 0
fi

matrix=$(echo "$repos" | jq --arg org "$bot_org" '[.[] | {
  repo: .repo,
  owner: (.repo | split("/")[0]),
  name:  (.repo | split("/")[1]),
  fork:  ($org + "/" + (.repo | split("/")[1])),
  locales_path:      .locales_path,
  file_format:       .file_format,
  source_language:   .source_language,
  framework:         (.framework // ""),
  setup:             (.setup // ""),
  extract:           (.extract // ""),
  format:            (.format // ""),
  branch_prefix:     (.branch_prefix // "translate"),
  pr_title_prefix:   (.pr_title_prefix // "chore:"),
  context_audit:     (.context_audit // false),
  source_paths:      ((.source_paths // []) | join(",")),
  default_reviewers: ((.default_reviewers // []) | join(",")),
  language_reviewers: ((.language_reviewers // {}) | to_entries | map(.key + "=" + .value) | join(",")),
  feedback_allowlist: ((.feedback_allowlist // []) | join(","))
}]')

echo "$matrix" | jq .

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "repos=$(echo "$matrix" | jq -c .)" >> "$GITHUB_OUTPUT"
  echo "bot_org=$bot_org" >> "$GITHUB_OUTPUT"
  echo "bot_user=$bot_user" >> "$GITHUB_OUTPUT"
  echo "bot_email=$bot_email" >> "$GITHUB_OUTPUT"
fi
