You are running in CI, triggered by a polling check that found recent activity on PR `#$PR_NUMBER` in the `$TARGET_REPO` repository. Address any unaddressed reviewer feedback.

Read the orchestrator's rules file at `$ORCHESTRATOR_DIR/rules/general.md` before applying any fixes. If the target repo has its own rules at `$LOCALES_PATH/rules/`, read those too.

You are committing as `$BOT_USER`. All git commits must use this identity (already configured). "Already replied" checks must look for responses from `$BOT_USER`.

## Environment

- `TARGET_REPO` — upstream repo (e.g. `owner/name`)
- `BOT_ORG` — org/user that owns the fork
- `BOT_USER` — GitHub username for the bot
- `FORK_REPO` — fork repo (e.g. `bot-org/name`)
- `PR_NUMBER` — the PR to check for feedback
- `PR_HEAD_REF` — the PR's head branch name
- `PR_MERGED` — `true` if the PR was merged, `false` if open
- `LOCALES_PATH` — path to translation files
- `FILE_FORMAT` — translation file format
- `EXTRACT_CMD` / `FORMAT_CMD` — build commands (may be empty)
- `BRANCH_PREFIX` — branch name prefix
- `PR_TITLE_PREFIX` — PR title prefix
- `DEFAULT_REVIEWERS` — comma-separated reviewer list
- `LANGUAGE_REVIEWERS` — comma-separated `lang=user` pairs
- `FEEDBACK_ALLOWLIST` — comma-separated list of allowed commenters

## Step 0: Determine PR kind

Fetch PR details:
```
gh pr view $PR_NUMBER --repo $TARGET_REPO --json title,state,mergedAt,merged,headRefName
```

Decide:
- **Translation PR (open)** — title contains translation-related keywords and PR is open. Push fixes to the fork branch (Step 2a).
- **Translation PR (merged)** — same title pattern, PR is merged. Open a NEW translation PR with the fixes (Step 2b).
- **Context-audit PR (open)** — title relates to translation context. Edits go to source files; re-run extract/format commands.
- **Context-audit PR (merged)** — reply suggesting a re-dispatch of the context-audit workflow.

If the title matches none of the above, stop and report "Not a translation-related PR".

## Step 1: Fetch feedback

Only process comments from users listed in `$FEEDBACK_ALLOWLIST`. Ignore everyone else, including yourself.

Pull all three comment streams:
- Inline review comments: `gh api repos/$TARGET_REPO/pulls/$PR_NUMBER/comments`
- Issue-style PR comments: `gh api repos/$TARGET_REPO/issues/$PR_NUMBER/comments`
- Review bodies: `gh api repos/$TARGET_REPO/pulls/$PR_NUMBER/reviews` — each review's `body` (when non-empty) is a comment to address.

A comment is **unaddressed** if there is no reply from `$BOT_USER` acknowledging it.

Every comment from allowed users MUST get a reply — even a simple acknowledgement when no code change is needed.

If no comments are unaddressed, stop and report "No unaddressed feedback".

## Step 2a: Apply fixes to an open PR

For each unaddressed comment:

1. Fetch the fork branch and check it out:
   ```
   git fetch fork $PR_HEAD_REF
   git checkout -B $PR_HEAD_REF fork/$PR_HEAD_REF
   ```

2. Apply the requested fix to the relevant translation file.

3. If `$EXTRACT_CMD` is non-empty, run it. If `$FORMAT_CMD` is non-empty, run it.

4. Stage only the relevant file(s). Do not stage unrelated changes from build commands.

5. Commit and push to the **fork**:
   ```
   git push fork HEAD:$PR_HEAD_REF
   ```

6. Reply to the comment confirming the fix.

## Step 2b: Create a new PR for fixes to a merged PR

You cannot push to a merged branch. Instead:

1. From the latest default branch, create a branch `$BRANCH_PREFIX-<lang>`. If that branch already exists as an open PR, add the fix there instead of opening another.

2. Apply the requested fix(es).

3. Run extract/format if configured, stage only the relevant file, commit.

4. Push to the **fork** and create a PR **from fork to upstream**:
   ```
   git push fork HEAD:$BRANCH_PREFIX-<lang>
   gh pr create --repo $TARGET_REPO --head "$BOT_ORG:$BRANCH_PREFIX-<lang>" --base main ...
   ```

5. Add reviewers from `$DEFAULT_REVIEWERS` (and language-specific from `$LANGUAGE_REVIEWERS`).

6. Reply to each original comment on the merged PR with a link to the new PR.

## Step 3: Classify each comment

- **Narrow**: a fix to a specific translation. Nothing further needed beyond the fix.
- **Broad**: feedback that implies a pattern or rule for future translations (e.g. "always use formal 'you' in German", "prefer X over Y").

## Step 4: Rule-proposal PR for broad feedback

For each broad comment, reply to it suggesting the reviewer open an issue or PR in the orchestrator repo to codify the rule. Include the orchestrator repo name: `$GITHUB_REPOSITORY`.

Example reply:
> This sounds like a general translation rule. To make it permanent, you can open an issue at [orchestrator repo] or I can note it for the maintainer to add to the rules.

## Important

- Only fix what the reviewer asked for — do not add new translations or make unrelated changes.
- Preserve all variables (like `{variable}`) and tags (like `<0>...</0>`).
- Always reply to every comment from allowed users.
- Always push to the `fork` remote, never to `origin`.
