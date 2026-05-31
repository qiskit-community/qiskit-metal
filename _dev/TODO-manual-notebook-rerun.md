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

## Why bother?

Stale outputs are the silent killer of a docs site's trust. A reader
seeing `<Figure size 2400x1000 with 2 Axes>` instead of an actual figure,
or an old "Qiskit Metal" watermark instead of "Qiskit / Quantum Metal,"
looks unmaintained. The automation closes the loop: every PR that touches
the rendering path or a tutorial's logic re-runs the relevant notebooks
and we either commit the new outputs or fix the regression that broke
them.
