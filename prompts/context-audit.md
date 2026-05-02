You are running in CI to audit translatable strings in source files. Your goal is to add translator-facing `context` annotations only where ambiguity is real, and to keep translation file bloat minimal by reusing existing context phrases.

Read all rules files before starting. Rules are in the orchestrator repo:
- General rules (apply to all repos): `$ORCHESTRATOR_DIR/rules/general/` — read every `.md` file in this directory.
- Repo-specific rules: `$ORCHESTRATOR_DIR/rules/$TARGET_REPO/` — read every `.md` file in this directory if it exists.

You are committing as `$BOT_USER`. All git commits must use this identity (already configured).

## Environment

- `TARGET_REPO` — upstream repo
- `BOT_ORG` / `BOT_USER` / `FORK_REPO` — bot identity and fork
- `LOCALES_PATH` — path to translation files
- `FILE_FORMAT` — translation file format
- `SOURCE_PATHS` — comma-separated glob patterns for source files to scan
- `FRAMEWORK` — i18n framework (e.g. `svelte-lingui`, `react-i18next`, `vue-i18n`)
- `EXTRACT_CMD` / `FORMAT_CMD` — build commands (may be empty)
- `BRANCH_PREFIX` — branch name prefix
- `PR_TITLE_PREFIX` — PR title prefix
- `DEFAULT_REVIEWERS` — comma-separated reviewer list

## Step 1: Skip if a context-audit PR is already open

```
gh pr list --repo $TARGET_REPO --state open --author $BOT_USER --json number,title \
  --jq '[.[] | select(.title | test("context"))]'
```

If there is already an open context-audit PR, stop and report "A context-audit PR is already open."

## Step 2: Build a context inventory

Scan source files matching `$SOURCE_PATHS` patterns. Based on `$FRAMEWORK`, look for the appropriate i18n function calls:

- **svelte-lingui**: `$t\`...\`` and `$t({ message: "...", context: "..." })`
- **react-i18next**: `t("key")`, `t("key", { context: "..." })`, `<Trans>` components
- **vue-i18n**: `$t("key")`, `t("key")`
- **Other**: scan for common i18n patterns (`t()`, `i18n()`, `translate()`, `gettext()`)

Build a map of:
- **Already-annotated entries**: calls that already have a `context` parameter
- **Unannotated entries**: calls without `context`

## Step 3: Decide what needs a context

Ambiguity criteria, in priority order:

1. **Same key/string used in 2+ places with divergent meanings** (e.g. "Cancel" as a modal dismiss vs. "Cancel" to abort an operation).
2. **Commonly ambiguous short words** (3 words or fewer): `Right`, `Left`, `Close`, `Open`, `Back`, `Save`, `Cancel`, `Continue`, `Skip`, `Done`, `New`, `Edit`, `View`, `Clear`, `Run`, `Set`, `Show`, `Hide`, `OK`, `Remove`, `Reset`, `Retry`, `Verify`, `Default`, `Upgrade`.
3. **Generic labels** that could refer to multiple things: `Name`, `Type`, `Status`.

Skip everything else. Long phrases (>5 words), file names, URLs, and clearly self-disambiguating strings are NOT candidates.

**When in doubt, skip it.** A missing annotation is cheap to add later; an unnecessary one permanently bloats translation files.

## Step 4: Pick a context, preferring reuse

1. If an already-annotated call site of the same string has a matching context, reuse it **byte-for-byte**.
2. If multiple unannotated call sites share the same UI role, assign them all the same new phrase.
3. Only invent a new phrase when no existing one fits. Use concise, translator-facing descriptions: `"button label: dismiss dialog"`, `"menu item: delete passkey"`, `"direction"`.

## Step 5: Apply the conversions

Convert each call site to include the `context` parameter, following the conventions of `$FRAMEWORK`. Do not change anything else — no copy changes, no translation edits, no unrelated refactors.

### Budget

No more than **40 annotations per sweep**. If more candidates exist, pick the highest-impact ones. Remaining candidates will be picked up in a future sweep.

## Step 6: Extract and format

If `$EXTRACT_CMD` is non-empty, run it. If `$FORMAT_CMD` is non-empty, run it. New context-annotated entries will appear in translation files (possibly with empty translations — those will be picked up by the translation check workflow).

## Step 7: Open the PR

1. Branch: `$BRANCH_PREFIX-context` from latest default branch.
2. Stage both source file changes and translation file changes.
3. Commit and push to **fork**:
   ```
   git push fork HEAD:$BRANCH_PREFIX-context
   ```
4. Open the PR **from fork to upstream**:
   ```
   gh pr create \
     --repo $TARGET_REPO \
     --head "$BOT_ORG:$BRANCH_PREFIX-context" \
     --base main \
     --title "$PR_TITLE_PREFIX add translation context" \
     --body "..."
   ```

   Body format:
   ```
   Adds translator-facing `context` annotations to ambiguous translatable strings so translators can produce distinct translations per UI role.

   # Changes

   - Converted <N> occurrences across <M> files to include context
   - Reused existing context phrases for <K> of them (no new translation entries)
   - Introduced <L> new context phrases
   <if budget hit:>
   - Budget reached at 40 annotations; <count> additional candidates deferred to next sweep
   ```

5. Add reviewers: `gh pr edit <number> --repo $TARGET_REPO --add-reviewer <$DEFAULT_REVIEWERS>`.

## Important

- Do not change translations or user-visible copy — only add context annotations to source files.
- Reuse existing context phrases byte-for-byte.
- When in doubt, skip the annotation.
- One PR for the whole sweep.
- Always push to the `fork` remote, never to `origin`.
