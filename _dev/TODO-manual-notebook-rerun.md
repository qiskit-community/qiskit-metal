# Manual notebook re-exec needed (skipped from automated merge)

After the v0.7.0 `docs/tut/` rename + headless rewrite, 7 notebooks have output
gaps that **could not be recovered** by the automated cell-source-match merge
(commit `22cf0460a`). These cells were structurally rewritten — their source no
longer matches the original `tutorials/` version, so no output transplant is
possible.

The only fix is to **re-execute** these notebooks in a live Jupyter kernel and
commit the fresh outputs.

## Notebooks needing re-exec

| Notebook | Output gap | Image gap |
|---|---|---|
| `docs/tut/1-Overview/1.1-Bird's-eye-view-of-Qiskit-Metal.ipynb` | +1 | +1 |
| `docs/tut/1-Overview/1.4-Headless-quick-view-(no-Qt-GUI).ipynb` | +6 | +3 |
| `docs/tut/1-Overview/1.6-QComponent-shape-library.ipynb` | +1 | 0 |
| `docs/tut/2-From-components-to-chip/2.11-Routing-101.ipynb` | +4 | +4 |
| `docs/tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip.ipynb` | +2 | +2 |
| `docs/tut/2-From-components-to-chip/2.23-Modify-chip-options.ipynb` | +3 | -1 |
| `docs/tut/3-Renderers/3.5-Render-your-design-to-Gmsh.ipynb` | +2 | +1 |

(Gaps are vs. `tutorials/` reference. `2.23` has 1 MORE image in `docs/tut/`
already — re-exec should reconcile in favor of whichever is correct.)

## How to re-run

**Option A — interactive (recommended for the GUI-touching ones):**
```bash
uv run --group jupyter jupyter lab docs/tut/
# Open each notebook in the table, Cell → Run All, save, commit
```

**Option B — batch headless (faster, but won't run cells needing MetalGUI):**
```bash
# Per-notebook (replace path):
uv run --group jupyter jupyter nbconvert --to notebook --inplace --execute \
    "docs/tut/1-Overview/1.4-Headless-quick-view-(no-Qt-GUI).ipynb"
```

`1.1`, `1.4`, `1.6`, `2.11`, `2.21`, `2.23` should all run cleanly headless
(they were rewritten to use `qm.view()` instead of `MetalGUI`). `3.5 Gmsh`
needs `gmsh` installed (`pip install gmsh` or `uv pip install gmsh`).

## Why this can't be automated further

The merge tool (`_dev/merge_outputs.py`) matches cells by exact source code.
For these 7 notebooks, the headless rewrite changed enough of each cell that
no source match exists for the "rich-output" cells in `tutorials/`. A fuzzy
match would risk pasting wrong outputs onto altered code — silently
introducing misleading docs.

## After re-running

```bash
git add docs/tut/...   # the re-executed notebooks
git commit -m "docs(tut): re-execute 7 notebooks to populate outputs after restructure"
```

Then close this file as done.
