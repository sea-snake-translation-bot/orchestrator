#!/usr/bin/env bash
# Fails when a Claude run changed files the workflow does not allow it to.
#
# Usage: audit-claude-changes.sh <pre-refs-file> <allowed-pattern> [more...]
#
# Patterns are shell globs matched against paths relative to the repo root,
# e.g. `src/frontend/src/lib/locales/*` or `*.svelte`.
#
# Each local branch is compared against where it stood before the run. A branch
# Claude checked out from the fork has no entry in the snapshot, because it was
# not a local branch yet; its base is then the fork's ref as it stood before the
# run, so commits already on the pull request are not counted as this run's
# work. Only a branch the fork has never seen is compared against the trunk.
set -euo pipefail

pre_refs="${1:?usage: audit-claude-changes.sh <pre-refs-file> <allowed-pattern>...}"
shift
[ "$#" -gt 0 ] || { echo "No allowed patterns given." >&2; exit 2; }

if [ ! -f "$pre_refs" ]; then
  echo "No ref snapshot at $pre_refs — nothing to audit."
  exit 0
fi

sha_for() { grep "^$1=" "$pre_refs" 2>/dev/null | cut -d= -f2 || true; }

violations=()
while IFS='=' read -r ref sha; do
  pre_sha=$(sha_for "$ref")
  [ -n "$pre_sha" ] || pre_sha=$(sha_for "fork/$ref")

  if [ -z "$pre_sha" ]; then
    base="origin/main"
  elif [ "$pre_sha" != "$sha" ]; then
    base="$pre_sha"
  else
    continue
  fi

  files=$(git diff --name-only "$base..$sha" 2>/dev/null || true)
  [ -z "$files" ] && continue

  while IFS= read -r f; do
    [ -n "$f" ] || continue
    allowed=false
    for pattern in "$@"; do
      # shellcheck disable=SC2254 -- the pattern is meant to glob
      case "$f" in $pattern) allowed=true; break ;; esac
    done
    [ "$allowed" = true ] || violations+=("$ref: $f")
  done <<< "$files"
done < <(git for-each-ref --format='%(refname:short)=%(objectname)' refs/heads/)

if [ ${#violations[@]} -gt 0 ]; then
  echo "::error::Claude changed files this workflow may not change:"
  printf '  %s\n' "${violations[@]}"
  echo "::error::Allowed: $*"
  exit 1
fi

echo "Audit passed — every change this run made matches: $*"
