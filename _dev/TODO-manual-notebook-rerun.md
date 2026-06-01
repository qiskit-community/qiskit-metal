# Notebook output refresh — automated + manual lanes

The published docs site shows the cached `outputs` of each `.ipynb` file
(stored figures, printed values, error traces). They go stale whenever the
API surface, renderer, or visual brand changes. Two lanes for refreshing
them:

## 🟢 Auto-runnable — `_dev/rerun_auto.py`

Everything listed in `_dev/auto-runnable-notebooks.txt` (a comment-friendly
whitelist) re-executes against the **lite install** (`pip install
quantum-metal[gui]`, no Ansys / gmsh) on every PR via the
`tests-lite → Execute whitelisted tutorial notebooks` CI job.

Local refresh:

```bash
# Dry-run — show what would execute
uv run python _dev/rerun_auto.py

# Actually run, 4 in parallel
uv run python _dev/rerun_auto.py --run

# Filter to a section
uv run python _dev/rerun_auto.py --run --filter 1-Overview

# After execution, sync the tutorials/ mirror so both folders match
uv run python _dev/sync_two_folders.py --write
```

When a notebook fails on CI, the first instinct should be **"is the
notebook broken or did the test surface a real regression?"** The former
is rare; the latter is what this gate exists for.

## 🟡 External-gated — manual re-run only

Notebooks needing Ansys HFSS/Q3D, gmsh, KLayout, or a real fab GDS file
are **not** in the whitelist. They keep their committed outputs from the
maintainer's last manual run. The reference list lives at the bottom of
`_dev/auto-runnable-notebooks.txt` in the "External-gated" comment block.

When one of those tools changes (Ansys version bump, gmsh upgrade, etc.):

1. Install the relevant extras: `pip install "quantum-metal[ansys]"` or
   `pip install "quantum-metal[mesh]"`.
2. Open the notebook in JupyterLab and re-run cells manually.
3. Sync: `python3 _dev/sync_two_folders.py --write`.
4. Commit.

## 🟠 Interactive-only

Anything that requires a Qt event loop (mouse clicks, modal dialogs) can't
be programmatically re-run. These are rare; currently none in the numbered
tutorials.

## Deferred follow-ups

These came up during the PR-#1095 design discussion and are worth doing
later, but aren't blockers for the v0.7.2 release:

1. **Post-merge manual Qt-screenshot refresh.** Once this PR lands, the
   new branding (Qiskit / Quantum Metal title bar, watermark fix, factory
   import, etc.) won't be reflected in the frozen Qt-screenshot tutorials
   until someone opens each in a local Qt session and re-runs cells.
   Suggested sweep: 1.1, 1.2, 1.3, 2.01, 2.21 — one focused commit on
   `main` after merge.

2. **Option E — on-demand Xvfb + `[gui]` CI job.** A `workflow_dispatch`
   job that spins up Xvfb on ubuntu-24.04, installs `quantum-metal[gui]`,
   and runs the frozen-Qt set with real Qt windows. Outputs ship as a
   downloadable workflow artifact (zip) for the maintainer to diff
   against committed screenshots and selectively replace. Caveats: Qt
   session dock geometry defaults to a less-polished layout than a
   hand-arranged maintainer session, so auto-refreshed screenshots tend
   to look visually inferior. The job is useful mostly as a safety net
   (a) when nobody with a Qt setup is available to refresh manually, or
   (b) to demonstrate the Xvfb + lite-Colab path works for users
   following Onri-style headless install scripts.

## Why bother?

Stale outputs are the silent killer of a docs site's trust. A reader
seeing `<Figure size 2400x1000 with 2 Axes>` instead of an actual figure,
or an old "Qiskit Metal" watermark instead of "Qiskit / Quantum Metal,"
looks unmaintained. The automation closes the loop: every PR that touches
the rendering path or a tutorial's logic re-runs the relevant notebooks
and we either commit the new outputs or fix the regression that broke
them.
