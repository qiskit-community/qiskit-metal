# Automated maintainer bot — policy

This repository uses an automated maintainer to handle a portion of
incoming issues and pull requests. This file explains what the bot
does, what it doesn't do, and how to interact with it.

## Who runs the bot

The bot is an instance of the official [Anthropic Claude
GitHub App](https://github.com/apps/claude). It posts as
**`claude[bot]`** (or a similar generic identity), not under any
human's name. It is configured and operated by the
**Quantum Metal and QDC maintainers**.

The bot acts within the scope and limits defined in
[`.claude/AGENT.md`](../.claude/AGENT.md) (the governance file,
checked into this repo and version-controlled like any other code).

## What the bot does

For incoming **issues**:

- **Triages** — applies labels from a locked taxonomy
  (`type/*`, `area/*`, `needs-*`, etc.)
- **Replies** with relevant context, links to docs, requests for
  reproducer when needed
- **Routes** issues that require special expertise (HFSS / AEDT /
  pyaedt / Ansys hardware) into a `needs-hardware-review` queue
  for the human maintainer

For incoming **pull requests**:

- May leave a comment summarizing the change or flagging concerns
- Does **not** approve, request changes, or merge

For repository **maintenance**:

- May open small draft PRs for clear, low-risk fixes (single-file,
  no public API changes, no test-file modifications, not in any
  hard-touch zone). All bot PRs are **drafts** until a human
  reviewer converts them.

## What the bot does NOT do

- **Never merges PRs.** A human always clicks the merge button.
- **Never modifies test files** when fixing a bug. It may add new
  tests, not edit existing ones.
- **Never changes public API signatures** (renames, signature
  changes, removals).
- **Never touches "hard-touch" zones** — the HFSS/Q3D renderers,
  the `_gui/` subtree, the pyEPR integration bridge, tutorial
  notebooks, CI workflows, `pyproject.toml`. These all require
  human review.
- **Never executes commands or fetches URLs from user content.**
  Issue and comment bodies are treated as data, not instructions.
- **Never reveals secrets, env vars, or credentials.**
- **Never pushes to `main` directly.** Only `claude/*` branches,
  through PRs that respect branch protection.

## What to expect as an issue reporter

If you open an issue:

- The bot will usually respond within minutes with a triage
  comment and labels
- A human maintainer reviews bot triage within **~7 days**
- For anything labeled `needs-hardware-review`, expect a longer
  wait — these need an Ansys-equipped reviewer
- The bot's reply is a starting point, not a final answer. If
  the bot misunderstood your issue, just reply — a human will
  see it on the next review pass

If you want to reach a human directly:

- Tag a maintainer in your comment, or open a GitHub Discussion
- Or use the project's Discord: https://discord.gg/kaZ3UFuq
  (community channel; please use SECURITY.md for security
  reports, not Discord)

## What to expect as a PR author

- The bot may leave a triage comment but **does not** approve or
  merge your PR
- The standard CI checks gate merge as usual
- A human maintainer reviews PRs at their normal cadence
- The CLA bot (`cla-assistant.io`) is separate from this bot and
  is required for first-time contributions

## Opting out

The bot acts on every public issue and PR by default. If you have
a sensitive issue (security vulnerability, private data, etc.):

- For security issues, please follow the security policy in
  `SECURITY.md` if present, or contact the maintainers via the
  contact channels listed there
- For other sensitive matters, contact the maintainers via the
  project's listed contact channels before opening a public
  issue

## Accountability

- All bot actions are logged in the GitHub Actions audit log and
  in daily summary files at `.claude/audit/YYYY-MM-DD.md` (when
  the bot can write them)
- The bot is bound by the rules in [`.claude/AGENT.md`](../.claude/AGENT.md);
  governance changes go through human-authored PRs
- If you see the bot misbehave (wrong labels, inappropriate
  replies, unsafe PRs), report it by tagging a maintainer in a
  comment, opening a GitHub Discussion, or via the project
  Discord

## Why automate maintenance at all

Quantum Metal is a small, community-maintained library with a
single principal maintainer and a growing user base. Automation
handles routine triage so the human maintainer can focus on the
work that requires judgement: HFSS validation, architectural
decisions, code review of substantive PRs, and supporting the
community on Discord.

The intent is to **respond faster** and **route more
predictably** — not to replace human maintainer presence. If
the experience feels less personal as a result, please push back
and we'll adjust.
