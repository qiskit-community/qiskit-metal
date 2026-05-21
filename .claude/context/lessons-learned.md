# Lessons learned — quantum-metal hard-won fixes

Every entry here is a real bug I (or a previous agent) shipped a fix
for. Reading this first saves you hours of re-discovering the same
walls from scratch.

Each entry: **symptom → cause → fix → reference commit / PR / test
where applicable**.

## Python / packaging

### `uv run` auto-syncs the venv

**Symptom**: You install a custom set of deps with `uv pip install
foo bar` then later run `uv run python -c "..."` — and uv silently
installs 80+ packages from `pyproject.toml`, overwriting your custom
set.

**Cause**: Inside a `uv`-managed project, `uv run` calls `uv sync`
first. The flag `--no-sync` warns *"has no effect when used outside
of a project"* if you're outside a project dir, but the side-effect
applies regardless.

**Fix**: For custom-installed venvs, invoke `.venv/bin/python`
directly. Never use `uv run` if you've manually set up the venv
contents.

**Reference**: `.github/workflows/main.yml` `tests-lite` job uses
`.venv/bin/python -m pytest …`, NOT `uv run pytest`. PR #1060 commit
that fixed this is the cautionary tale.

### `uv venv` doesn't ship `pip`

**Symptom**: `.venv/bin/python -m pip install foo` fails with
`No module named pip`.

**Cause**: `uv venv` builds a minimal venv without pip — uv is the
package manager.

**Fix**: Use `uv pip install foo` (uv-mode pip). Or
`uv pip install --python /path/to/venv/bin/python foo` if you need
to target a specific venv.

### `nbconvert --execute` uses kernel `python3` by default

**Symptom**: `jupyter nbconvert --execute notebook.ipynb` fails with
`No module named matplotlib` even though the venv has matplotlib.

**Cause**: nbconvert spawns the kernel named in the notebook
metadata. The default `python3` kernel points at the *system*
Python, not the venv.

**Fix**: Register the venv as a kernel and pass it explicitly:

```bash
.venv/bin/python -m ipykernel install --user --name my_kernel
.venv/bin/jupyter nbconvert --execute \
    --ExecutePreprocessor.kernel_name=my_kernel \
    notebook.ipynb
```

**Reference**: `tests-lite` CI job's `Execute headless tutorial
notebook` step (PR #1061).

### `json.dump(..., ensure_ascii=True)` (default) escapes unicode

**Symptom**: Re-saving a `.ipynb` you only made small edits to
produces a 1000-line diff full of `χ` instead of `χ` etc.

**Cause**: Python's `json.dump` defaults to ASCII-escaping all
non-ASCII characters. Jupyter writes notebooks with
`ensure_ascii=False` so they're readable; round-tripping with the
default flips them.

**Fix**: Always use `json.dump(..., ensure_ascii=False, indent=1)`
when round-tripping `.ipynb` files. Match Jupyter's format
exactly:

```python
with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")  # trailing newline
```

**Reference**: PR #1055 fixed an earlier notebook-fix script that
had this bug.

## Dependency-version traps

### pandas 2.2: integer indexing on string-labeled Series

**Symptom**: Code like `series[1]` works in dev but raises
`KeyError: 1` on a clean install.

**Cause**: pandas 2.2 removed the positional-fallback behavior for
integer indexing when the Series has non-integer labels. Was a
FutureWarning in 2.0/2.1.

**Fix**: Use `series.iloc[1]` for positional, `series[label]` for
label-based.

**Reference**: `src/qiskit_metal/renderers/renderer_mpl/mpl_renderer.py:299`
(`render_junction`). Surfaced when the lite venv pulled a newer
pandas than the dev env.

### qutip 5: `np.array([Qobj, ...])` no longer stacks

**Symptom**: Code that worked under qutip 4 returns an object-dtype
ndarray under qutip 5, and downstream math operations fail.

**Cause**: qutip 5 changed `__array__` so a list of `Qobj` becomes
a 1-D array of Python objects rather than a stacked numeric matrix.

**Fix**: Convert each `Qobj` to numpy explicitly before stacking:

```python
mat = np.array([q.full() for q in qobj_list])  # OK
```

**Reference**: `src/qiskit_metal/analyses/hamiltonian/states_energies.py`
(fixed in PR #1050).

### qutip 5: `np.absolute(Qobj)` no longer works

**Symptom**: Used to return a numpy array of magnitudes; now
raises.

**Fix**: Call `.full()` first: `np.absolute(qobj.full())`.

### HFSS 2024.1+: solution-type rename

**Symptom**: `o_design.GetSolutionType()` returns
`"HFSS Modal Network"` or `"HFSS Hybrid Modal Network"` instead of
`"DrivenModal"` on AEDT 2024.1+; downstream `== "DrivenModal"`
checks silently fall through.

**Cause**: Ansys renamed the strings. Same for Driven Terminal.

**Fix**: pyEPR ≥ 0.9.5 normalises `design.solution_type` at read
time, so most call sites are insulated. The exception is metal's
own `set_mode` in `hfss_renderer.py` which calls
`o_design.GetSolutionType()` directly — that needs the predicate
helpers in `solution_types.py` (`is_drivenmodal`, `canonical_kind`,
etc.).

**Reference**:
- `src/qiskit_metal/renderers/renderer_ansys/solution_types.py`
- `tests/test_solution_types.py`
- pyEPR PRs #172, #176

### `numpy<2` pin is real

**Symptom**: `pip install quantum-metal` followed by `pip install
numpy>=2` downgrades or breaks something.

**Cause**: Some transitive dep (suspected: pyaedt or qutip 5
intermediate) requires `numpy<2`. Hasn't been root-caused.

**Fix**: Until identified and upstream-resolved, the pin stays.
Don't relax it casually.

### `pyaedt<0.24` is a temporary pin

**Symptom**: pyaedt 0.24 was buggy as of Jan 2026.

**Cause**: noted in `pyproject.toml` comment.

**Fix**: Retest periodically. As of v0.6.1 the pin is still in
place; AWS Palace integration is the intended unblock for the
broader pyaedt situation.

## Qt / GUI / lazy-import

### `import qiskit_metal` used to require PySide6

**Symptom**: pre-v0.6.1, even setting `QISKIT_METAL_HEADLESS=1`
would import `PySide6` at module load.

**Cause**: `__setup_Qt_backend()` was called unconditionally at
the bottom of `src/qiskit_metal/__init__.py`.

**Fix (v0.6.1)**: Moved to opt-in `setup_qt_backend()`
(idempotent), called automatically from `MetalGUI.__init__`.
Top-level `MetalGUI` and `plt` are now lazy via PEP-562
`__getattr__`. PySide6 imports in `mpl_interaction.py` are wrapped
in `try/except ImportError` with `_require_qt()` gates on the
functions that use them.

**Reference**: PR #1060. Verify with:

```bash
QISKIT_METAL_HEADLESS=1 python3 -c "
import sys
class B:
    def find_spec(self, name, path, target=None):
        if name.startswith('PySide6'):
            raise ImportError(f'BLOCKED: {name}')
        return None
sys.meta_path.insert(0, B())
import qiskit_metal as qm
fig = qm.view(qm.designs.DesignPlanar())
print('OK without PySide6')
"
```

### `QMplRenderer.canvas` is unused

**Symptom**: You might think decoupling `QMplRenderer` from Qt
requires a refactor of `PlotCanvas` interactions.

**Cause**: It doesn't — `self.canvas` is stored on the instance
and **never read by any method**.

**Fix**: Make the `canvas` constructor arg optional. Done in
v0.6.1.

### `QMplRenderer.get_mask` had a silent bug

**Symptom**: `hidden_layers={1}` had no effect when combined with
hidden components.

**Cause**: Two consecutive `mask = ...` lines, the second
overwriting the first.

**Fix**: OR the two filters. Now `mask = ... | ...`.

**Reference**: `src/qiskit_metal/renderers/renderer_mpl/mpl_renderer.py`
(PR #1060 fix). Caught by the new `test_view_hides_layers` test.

### `_start_renderers` crashed on missing optional deps

**Symptom**: `DesignPlanar()` raised `ModuleNotFoundError: No
module named 'gmsh'` on lite installs.

**Cause**: `_start_renderers` called `importlib.find_spec` (which
succeeds because the renderer module exists in our source tree)
then `importlib.import_module` (which fails because the EXTERNAL
package isn't installed).

**Fix**: Wrap `import_module` in `try/except ImportError`, log
clear info pointing at the appropriate extras (`[fem]`,
`[ansys]`).

**Reference**: `src/qiskit_metal/designs/design_base.py`
`_start_renderers` (PR #1060).

## Release / CI

### v0.6.0 tag exists but PyPI never received 0.6.0

**Symptom**: GitHub tag `v0.6.0` exists with a published release
page, but `pip install quantum-metal` still gets 0.5.4.

**Cause**: The `bump-version` workflow failed at the
commit-and-tag step (`HTTP 409: Could not update file: Changes
must be made through a pull request`). Branch protection on `main`
blocks the workflow's direct Contents API write. Tag was somehow
created anyway (likely manually); it points at the v1054 merge
commit where `pyproject.toml` still says 0.5.4. When `release.yml`
fired from the tag push, `uv build` produced a `quantum-metal-0.5.4.whl`
and `uv publish` failed with *"version already exists"*.

**Fix** (applied for v0.6.1):
1. Open a regular PR that bumps `pyproject.toml` (+ `uv.lock`).
2. Merge via normal review flow.
3. Push tag pointing at the merge commit.

**Long-term fix**: Add `github-actions[bot]` to the branch-protection
bypass list (Settings → Branches → Edit rule for `main`). Then the
`bump-version` workflow works as written.

**Reference**: PR #1056, `.claude/commands/release.md`.

### `environment.yml` ↔ `pyproject.toml` drift

**Symptom**: conda users get older versions of qutip/scqubits/etc.
than pip users — silent runtime breakage.

**Cause**: Two files declared the same package's lower bound
independently. Drift accumulated across PRs.

**Fix**: `scripts/check_env_consistency.py` parses both, asserts
env.yml's allowed range ⊆ pyproject.toml's. Wired into CI as the
`env-consistency` job. First run caught 5 drifts (geopandas,
pandas, pint, shapely, pyaedt).

**Reference**: PR #1057.

### CLA bot fires on every Claude-authored PR

**Symptom**: Every PR Claude opens gets a CLA-bot comment within
seconds.

**Cause**: Default CLA gate on the repo, treats `claude` as a new
contributor.

**Fix**: Only the human can satisfy it. Mention it in PR
templates so users know to expect it.

## Tutorials / docs

### Notebook heading-level skips trip nbsphinx

**Symptom**: Sphinx docs build prints `CRITICAL: Title level
inconsistent` for many tutorial notebooks.

**Cause**: Tutorial authors used `#` then `###`, skipping `##`.
nbsphinx renders these to RST with corresponding heading levels;
RST requires the hierarchy to be contiguous.

**Fix**: Programmatic normalisation script (track parent depth via
a stack, demote skipped levels to parent+1). Applied to 26 of 40
notebooks in PR #1055.

### Sphinx "document isn't included in any toctree" for `apidocs/`

**Symptom**: ~100 warnings on every docs build.

**Cause**: `apidocs/` contains auto-generated per-class stub
files that are only linked from module pages, not the main
toctree.

**Fix**: Add a hidden `:glob:` toctree at the bottom of
`docs/index.rst`:

```rst
.. toctree::
    :hidden:
    :glob:

    apidocs/*
```

**Reference**: PR #1055.

### CONTRIBUTING.md was telling people to use pylint+yapf

**Symptom**: New contributors' PRs failed lint because they used
the wrong tools.

**Cause**: The guide hadn't been updated since the ruff migration.

**Fix**: Updated to ruff with `charliermarsh.ruff` VSCode
extension. PR #1057.

## Ruff findings worth knowing

### `is 0` / `is 1` worked by accident

**Symptom**: ruff F632 flags `len(polys) is 2`, `xoff is 0`, etc.

**Cause**: CPython interns small integers, so `5 is 5` returns
True coincidentally. Per the language spec this is undefined.

**Fix**: Change to `==`. Was a real bug that happened to not
manifest. PR #1055 fixed 5 instances.

### 13 deferred ruff findings live in HFSS/`_gui/`

**Symptom**: `uvx ruff check src` reports 13 errors.

**Cause**: All in do-not-touch zones (E711 None-comparisons in
`renderer_ansys_pyaedt`, E721 type comparisons in `_gui/`, an
F811 dead `render_chip` stub in `ansys_renderer.py:1053`).

**Fix**: Resolved by PR #1070 (community ruff sweep by
PositroniumJS). Validated by CI on the lite path; HFSS / Qt
runtime paths *not* validated (no AEDT in CI). Behavioral
equivalence is theoretically sound for every change except
one — see the next entry.

### PR #1070 wirebond filter — watch this if HFSS issues land

**Where**: `src/qiskit_metal/renderers/renderer_ansys/ansys_renderer.py:1624-1625`
(the `add_wirebond` path on `QAnsysRenderer`).

**What changed**: Ruff rule E712 rewrote two pandas DataFrame
filter expressions:

```python
# before
wb_table  = table.loc[table["hfss_wire_bonds"] == True]
wb_table2 = wb_table.loc[wb_table["subtract"] == True]
# after
wb_table  = table.loc[table["hfss_wire_bonds"]]
wb_table2 = wb_table.loc[wb_table["subtract"]]
```

**Why this needs an entry**: For a pandas column with
`dtype=bool`, the two forms are identical — both select rows
where the value is True. **But** if the qgeometry column ever
holds non-bool truthy values (Python `1`, the string `"True"`,
etc. from a misconfigured component), the two forms diverge:
`== True` is exact equality (matches only literal True);
the bare mask uses Python truthiness (matches any truthy).

The qgeometry tables *should* always be bool-typed for these
flags, and CI is green — but CI can't actually exercise the
HFSS wirebond path (no AEDT license).

**What to do if a bug report lands**:
1. Look for "wirebonds not appearing in HFSS" or "extra
   wirebonds" symptoms in `add_wirebond`.
2. Check the dtype of `table["hfss_wire_bonds"]` at the call
   site — if it's `object`, that's the problem.
3. Revert is one-liner: restore `== True` on both lines.

The pyaedt-side equivalent is commented-out code at
`renderer_ansys_pyaedt/pyaedt_base.py:887`, also rewritten by
PR #1070. Same caveat applies if/when that path is revived.

## Geometry / pin / HFSS-adjacent

### `LaunchpadWirebondDriven.in` pin normal points inward

**Symptom**: `test_pin_normals_point_outward` fails for
`LaunchpadWirebondDriven`.

**Cause**: The `driven_pin_line` `LineString` is constructed in
the same downward-y point order as its `main_pin_line`, but sits
on the opposite side of the pad — so both pins get a `+x` normal
even though `"in"` needs `-x`.

**Fix**: Swap the two points in `driven_pin_line`. Single-line
change. But it changes HFSS port orientation and needs Ansys
validation before landing.

**Reference**: `tests/test_qlibrary_pin_sanity.py`
`KNOWN_INWARD_PINS`. PR #1062.

### Pin `points` order determines the normal direction

**Symptom**: A new component's pin renders "the wrong way" in
HFSS — port plane inside the conductor.

**Cause**: `add_pin` computes the normal from the cross product
of the line tangent with z-up. Walking from point 0 to point 1,
the normal is "to the right" — flip the order and the normal
flips 180°.

**Fix**: Verify visually with `qm.view(design)` before relying on
HFSS results. Then use `test_pin_normals_point_outward` to gate
in CI.

## What this list doesn't include

Stuff that's NOT a "lesson learned" — those go in
`.claude/context/architecture.md` (how things are structured) or
`.claude/context/ecosystem.md` (why things are the way they are).
This file is **specifically things that bit us in production**.

When you fix a real bug, add an entry here. Future agents will
thank you.
