# /release — ship a new quantum-metal version to PyPI

This procedure ships a new release tag, GitHub Release page, and
PyPI artifact. **Read the v0.6.0 post-mortem (below) before
starting** — there's a real failure mode you need to avoid.

## The v0.6.0 post-mortem (cautionary tale)

v0.6.0 was supposed to ship via the `bump-version` workflow. It
failed silently:

1. The workflow tried to update `pyproject.toml` directly on `main`
   via the GitHub Contents API.
2. Branch protection on `main` rejected the write with `HTTP 409:
   Changes must be made through a pull request`.
3. The tag `v0.6.0` was created anyway (likely manually after the
   failure). It points at the v1054 merge commit where
   `pyproject.toml` still says `0.5.4`.
4. When `release.yml` fired from the tag push, `uv build` produced
   `quantum-metal-0.5.4.whl` and `uv publish` failed with
   "version already exists" — PyPI was never updated.

Result: GitHub Release page existed, tag existed, but `pip install
quantum-metal` still got 0.5.4.

**Fix applied for v0.6.1**: bump version via a regular PR. **Until
`github-actions[bot]` is added to the branch-protection bypass
list, the `bump-version` workflow doesn't work — use the manual
procedure below.**

## Procedure (when bump-version workflow is broken)

### 1. Pre-flight check

```bash
# Confirm main is green
mcp__github__list_commits --owner qiskit-community --repo qiskit-metal --sha main --perPage 1
# Run full test suite locally
QISKIT_METAL_HEADLESS=1 uv run pytest tests/
# Run the drift gate
uv run scripts/check_env_consistency.py
# Run lint
uvx ruff check src
```

All four must be clean. If any is red, fix before tagging.

### 2. Decide the version

- Patch bump (0.6.1 → 0.6.2): bug-fix-only release
- Minor bump (0.6.x → 0.7.0): new features, possibly breaking
- Major bump (0.x → 1.0): commit to API stability

Check `CLAUDE.md`'s status snapshot for what's queued.

### 3. Open the version-bump PR

```bash
git checkout main
git pull origin main
git checkout -b claude/bump-X.Y.Z

# Bump pyproject.toml
# (line 28-ish: version = "X.Y.Z")
# Bump uv.lock — find the quantum-metal entry (~line 2749) and
# update its version field
```

Both files MUST match exactly. The lockfile bump is the easy thing
to forget.

Commit and push:

```bash
git add pyproject.toml uv.lock
git commit -m "chore: bump version to X.Y.Z"
git push -u origin claude/bump-X.Y.Z
```

Open a PR via `mcp__github__create_pull_request` with title
`chore: bump version to X.Y.Z` and base `main`.

### 4. Wait for the user to merge

The CLA bot will block; only the human can satisfy it. **Don't
push the tag yet.**

### 5. Tag and push

After merge, on the user's go:

```bash
git checkout main
git pull origin main
# Confirm pyproject.toml says X.Y.Z at HEAD
grep '^    version' pyproject.toml

git tag vX.Y.Z origin/main
git push origin vX.Y.Z
```

This fires `release.yml` which:

- `uv build` → produces `quantum-metal-X.Y.Z-py3-none-any.whl`
  and `.tar.gz`
- `twine check` validates them
- Imports the wheel + sdist in isolation as a smoke test
- `uv publish` to PyPI via OIDC

### 6. Create the GitHub Release

Either:

- Via the GitHub UI: Releases → Draft a new release → tag
  `vX.Y.Z`, target `main`, title `vX.Y.Z`, body = release notes
  (curated, not auto-generated)
- Via `mcp__github__create_release` (if available)

Use the release-notes template from the v0.6.1 release as a
starting point — categorise by Compatibility / Bug fixes / Tests /
Docs / Hygiene / Compatibility matrix.

### 7. Post-release sanity check

```bash
# Wait ~2 min for PyPI to update
pip index versions quantum-metal   # should list the new version
# Or via WebFetch
WebFetch "https://pypi.org/pypi/quantum-metal/json" "what is the latest version?"
```

If PyPI still shows the old version, check the `release.yml` run on
GitHub Actions for errors.

### 8. Announce

The QDC Discord and the `#metal` Slack channel are the two places
the user typically announces. Generate a 3-sentence summary they
can post.

## Procedure (when bump-version workflow is fixed)

Once `github-actions[bot]` is added to the branch-protection
bypass list:

1. Go to https://github.com/qiskit-community/qiskit-metal/actions/workflows/bump-version.yml
2. Run workflow → version: `X.Y.Z`
3. Workflow bumps `pyproject.toml`, creates a commit on `main`,
   tags it, creates a draft GitHub Release, fires `release.yml`,
   publishes to PyPI.
4. Edit the draft release notes (auto-generated is too noisy).
5. Publish.

Then steps 7 + 8 above.

## Common pitfalls

### `uv.lock` not bumped

PyPI release goes out as the lockfile-declared version, not the
pyproject.toml version. Always update both.

### Tag name format

It's `vX.Y.Z` (lowercase v, no leading `release/` or `tag/`).
`release.yml` only fires on tags matching `v*`.

### Pre-release versions

For RCs use `vX.Y.Z-rc1` etc. — PyPI accepts these. Make sure they
parse as PEP 440 pre-releases or `twine check` rejects.

### Release notes vs auto-generated

GitHub's `--generate-notes` produces "what changed since last tag"
which is too granular. Always write curated notes that group by
theme.

### The CLA bot

Every PR Claude opens gets a CLA-bot comment. It blocks merge
until the human satisfies it. Mention this when handing the PR
off.

## Output format

When invoked, produce a short status report:

```markdown
## Release readiness — vX.Y.Z

- [ ] main is green
- [ ] tests pass locally (count: ...)
- [ ] env-consistency clean
- [ ] lint: 13 (deferred) / no new
- [ ] pyproject.toml + uv.lock bumped
- [ ] PR opened: #...
- [ ] PR merged → tag pushed
- [ ] PyPI shows X.Y.Z
- [ ] Release notes published
```

Mark items off as the user gates through. Don't skip steps.
