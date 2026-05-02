# sea-snake-translation-bot orchestrator

Centralized bot that automates translation maintenance for any public GitHub repo. No installation on target repos needed — just add an entry to `repos.yml`.

## How it works

1. Workflows in `.github/workflows/` run on cron schedules
2. `repos.yml` lists target repos and their i18n configuration
3. The bot forks each target repo under its own GitHub account
4. Translation work happens in the fork; PRs are opened against upstream
5. The bot has zero write access to any upstream repo — it is an external contributor

## Auth

Two secrets in this repo:

- `BOT_PAT` — classic PAT with `public_repo` scope from the bot's GitHub account
- `ANTHROPIC_API_KEY` — for Claude Code CLI

## Files

- `repos.yml` — managed repos and their per-repo config
- `scripts/` — bash helpers called by workflows
- `prompts/` — Claude prompts for translation tasks
- `rules/` — translation rules applied across all managed repos
- `.github/workflows/` — GitHub Actions entry points

## Adding a new repo

1. Add an entry to `repos.yml` (copy an existing one and adjust)
2. Push to `main`
3. Run the **Setup** workflow manually (or wait for the next 6-hour cron)
4. The bot forks the repo and begins translating on the next **Translate** run
