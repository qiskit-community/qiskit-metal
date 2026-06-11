# /health-check — repo health audit

Use this command to do a broad sanity check on the repo. It's
deliberately read-only — no changes get committed by default.

## What you're looking for

1. CI status of the most recent commits on `main`
2. Open PRs that look stale
3. Test count + recent flakiness
4. Lint findings — are they all in the known-deferred zones?
5. Dependency drift (`environment.yml` ↔ `pyproject.toml`)
6. Coverage on critical paths
7. Recent code changes that warrant attention
8. Dependabot alerts (if accessible)

## Procedure

Run these in parallel where possible.

### 1. CI status

```bash
# Most recent main commits + their statuses
mcp__github__list_commits --owner qiskit-community --repo qiskit-metal --sha main --perPage 5
# Or via gh if available
gh run list --branch main --limit 10
```

Look for: red runs, flaky retries, jobs that took unusually long.

### 2. Open PRs

```bash
mcp__github__list_pull_requests --owner qiskit-community --repo qiskit-metal --state open
```

Flag: PRs > 14 days old without recent activity. Don't auto-merge
or close — just report.

### 3. Local test count

```bash
QISKIT_METAL_HEADLESS=1 uv run pytest tests/ --collect-only -q | tail -5
QISKIT_METAL_HEADLESS=1 uv run pytest tests/ 2>&1 | tail -3
```

Compare against the baseline in `CLAUDE.md` status snapshot.
Investigate any drop in test count.

### 4. Lint

```bash
uvx ruff check src 2>&1 | tail -10
```

Expected output as of v0.6.1:

```
8  E721  type-comparison
6  E711  none-comparison
5  F811  redefined-while-unused
2  F405  undefined-local-with-import-star-usage
1  F822  undefined-export
Found 22 errors.
```

**13 of these are deferred** (HFSS / `_gui/` zones, see
`lessons-learned.md`). If the count changes:

- ↑ Someone added new lint debt. Look at the new findings;
  triage.
- ↓ Someone fixed deferred findings. Verify they had HFSS / Qt
  validation. If not, raise a flag.

### 5. Environment-drift gate

```bash
uv run scripts/check_env_consistency.py
```

Expect: `OK: 17 shared packages, no drift.` Any drift is a real
issue — see `lessons-learned.md` for context.

### 6. Coverage

The `coverage` CI job emits per-file coverage to the run's step
summary. Check it for the most recent main commit's run page.

Investigate:

- Files dropping below 30% coverage (something heavy was added
  without tests)
- New files at 0% (untested code shipped)

### 7. Recent activity heuristic

```bash
git log --oneline main -20
git log --since='2 weeks ago' --pretty=format:'%h %s' main
```

Skim for:

- Multiple "fix CI" commits in a row → flaky test or fragile
  infrastructure worth fixing
- Long stretches with no merges → release candidate window or
  branch protection issue
- Commit subjects that mention HFSS / Qt — verify they had
  appropriate validation

### 8. Dependabot

If you have repo access via the GitHub UI:

- https://github.com/qiskit-community/qiskit-metal/security/dependabot
- Note count, severity, oldest unhandled alert.

In a sandboxed agent context this often isn't accessible — note
the limitation in the report rather than guessing.

## Output format

Produce a short markdown report (under 300 words):

```markdown
## Repo health — <date>

**CI**: <green/red/flaky>, <last main commit sha + status>
**Tests**: <count> passing, <count> failing
**Lint**: <total findings>; <delta from baseline if any>
**Env drift**: <OK / list of drifts>
**Open PRs**: <count>, <oldest age>
**Dependabot**: <count if accessible, else "needs manual check">

### Things worth attention
- ...
- ...

### Things ready to do next
- ...
```

## What this command is NOT

- Not a fix-everything pass. Report and let the user decide.
- Not a release readiness check. For that use `.claude/commands/release.md`.
- Not a security audit. Dependabot covers that; this just surfaces
  the count.
