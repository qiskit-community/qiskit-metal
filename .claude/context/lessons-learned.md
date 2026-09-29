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

### pandas 2.0: `DataFrame.append` removed + gdstk positional-indexing a Series

**Symptom** (#1141): exporting a `RouteMeander` to GDS raised — first
`AttributeError: 'GeoDataFrame' object has no attribute 'append'`, then,
once that was fixed, `gdstk.boolean(...)` failed with
`Unable to retrieve item N from sequence operand2`. Only triggered when a
route had a lead segment shorter than the fillet radius, so it reached
`_fix_short_segments_within_table`.

**Cause**: two independent pandas-2 traps in the GDS renderer.
1. `df.append(row, ignore_index=False)` — `DataFrame.append` was removed in
   pandas 2.0. Replace with `pd.concat([df, row.to_frame().T])` (re-wrap in
   `geopandas.GeoDataFrame` to keep the geometry accessor).
2. `gdstk.boolean` iterates its operands by **position** (`operand[i]`), but
   `q_subtract_true` / `q_subtract_false` are pandas `Series` whose labels are
   not `0..n-1` (the short-segment path leaves duplicate/gapped index labels).
   `series[i]` is label-based, so gdstk's positional access raised `KeyError`.
   Fix: pass `list(series)` so gdstk sees a plain positional sequence.

**Fix**: `src/qiskit_metal/renderers/renderer_gds/gds_renderer.py` —
`_fix_short_segments_within_table` (concat instead of append) and
`_negative_mask` / `_positive_mask` (`list(...)` around the boolean operands).
Regression test: `tests/test_gds_short_segments.py` (exports a short-lead
meander and checks the area matches a low-fillet control).

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

### `numpy<2` pin: root cause and removal

**Symptom**: pairing numpy 2 with older compiled dependencies fails on
import. pandas < 2.2.2 raises `ValueError: numpy.dtype size changed,
may indicate binary incompatibility`, and pint < 0.24 raises
`AttributeError: module 'numpy' has no attribute 'cumproduct'`.

**Cause**: the `<2` cap came in with `pandas==1.5.3` (127656d4, May
2025). Wheels built against numpy 1.x are not ABI-compatible with
numpy 2. The cap survived after pandas moved to `>=2.1.1`, but 2.1.x
still predates numpy-2 wheels, so dropping the cap alone would have
let a resolver pair numpy 2 with an incompatible pandas.

**Fix** (Python 3.13/3.14 support): cap removed and floors raised to
the first numpy-2 builds: pandas 2.2.2, scipy 1.13.0, matplotlib
3.8.4, shapely 2.0.4, pint 0.24.4. pint 0.24.0–0.24.3 also break with
flexparser 0.4. Verified with `uv pip install --resolution
lowest-direct` under numpy 2.0.0 (py3.12) and numpy 1.24.2 (py3.11):
the failures match a newest-version run exactly (only missing
extras). If a floor is lowered, re-run that check.

### `pyaedt<0.24` stays on Python < 3.14

**Symptom**: pyaedt 0.24 was buggy as of Jan 2026.

**Cause**: noted in `pyproject.toml` comment. pyaedt 0.2x also
requires `numpy<2.3`, and numpy's first cp314 wheels are 2.3.2, so
the vetted range cannot install on 3.14.

**Fix**: environment markers. `>=0.21,<0.24` on Python < 3.14 and
`>=1.0.1` on 3.14. The pyaedt renderer is not validated against real
AEDT on 1.x; treat 3.14 + `[ansys]` as untested until someone runs it
with AEDT. AWS Palace integration is the intended unblock for the
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

### Tutorials lived in two folders until September 2026

Every notebook used to exist twice, `tutorials/` (names with spaces) and
`docs/tut/` / `docs/circuit-examples/` (hyphenated, for Sphinx), kept identical
by `_dev/sync_two_folders.py` and a CI check. Drift was the constant failure
mode, and the sync script itself once copied a stale notebook over a rewritten
one (its tiebreaker picked the wrong side after a rename in both trees). The
second tree was removed: `docs/` is the only copy and `tutorials/README.md`
maps old paths to new. Hyphenated names browse fine on GitHub and open fine in
JupyterLab and Colab, so the naming argument for two trees did not hold up.

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

### `autodoc_mock_imports` is not a pre-mock

**Symptom**: Adding `autodoc_mock_imports = ["PySide6", "gmsh", ...]` to
`docs/conf.py` isn't enough. Sphinx still crashes at `import qiskit_metal`
near the top of `conf.py` with `ModuleNotFoundError: No module named 'PySide6'`
(or `libEGL.so.1: cannot open shared object` if PySide6 is installed but its
native lib is absent).

**Cause**: `autodoc_mock_imports` only protects autodoc's cross-reference
walk — not `conf.py`'s own `import qiskit_metal` line, which fires before the
autodoc extension is fully active.

**Fix**: pre-install mocks into `sys.modules` BEFORE the `import qiskit_metal`
line in `conf.py`:

```python
import sys
from sphinx.ext.autodoc.mock import _MockModule

_MOCKED_MODULES = [
    "PySide6", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
    "qdarkstyle", "gmsh", "pyEPR", "pyaedt", "ansys",
    "ansys.aedt", "ansys.aedt.core",
    "IPython", "IPython.core", "IPython.core.magic", "IPython.display",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.qt_compat",
]
for _mod in _MOCKED_MODULES:
    sys.modules.setdefault(_mod, _MockModule(_mod))

import qiskit_metal  # now safe even with heavies absent
```

`autodoc_mock_imports` still belongs in `conf.py` for the cross-reference
walk; the pre-mock is additional.

### `unittest.mock.MagicMock` cannot be a class base

**Symptom**: After pre-mocking with `MagicMock`, build fails with
`TypeError: metaclass conflict: the metaclass of a derived class must be a
(non-strict) subclass of the metaclasses of all its bases`.

**Cause**: `_gui/widgets/all_components/table_view_all_components.py:41`
does `class QTableView_AllComponents(QTableView, QWidget_PlaceholderText)`.
When both bases are `MagicMock` instances, Python can't reconcile their
metaclasses.

**Fix**: use `sphinx.ext.autodoc.mock._MockModule`, not `unittest.mock.MagicMock`.
Sphinx's mock is purpose-built to be subclass-safe.

### tox env inheritance silently leaks `extras`

**Symptom**: Setting `[tool.tox.env.docs]` to lite (`dependency_groups = ["docs"]`
only, no `extras`) still installs PySide6/pyaedt/gmsh. Docs CI crashes on
`libEGL.so.1`.

**Cause**: `[tool.tox.env_run_base]` sets `extras = ["full"]` so the 9-combo
test matrix gets all heavies. Other envs **inherit this** unless they
explicitly override.

**Fix**: explicit empty list in the docs env config:

```toml
[tool.tox.env.docs]
    ...
    extras            = []        # REQUIRED, not optional
    dependency_groups = [ "docs" ]
```

Same applies to any other tox env that should NOT inherit base extras.

### Sphinx exit 2 vs "build succeeded"

**Symptom**: `sphinx-build` prints `build succeeded, N warnings.` and then
exits with code 2. CI marks the job failed. Locally, exit code is 0.

**Cause**: Sphinx exit code 2 means "build was interrupted" — some ERROR-level
event (typically a docutils ERROR, not a WARNING) caused a non-zero exit even
when the build technically produced output. Confusingly, the "build succeeded"
line is from a sub-step that finished before the ERROR-causing event.

**Fix**: look for `ERROR:` lines (not `WARNING:`) in the build log. Two common
sources:
1. **Inconsistent title style: skip from level X to Y** — RST/notebook heading
   hierarchy skipped a level. Fix by normalizing the underline characters or
   removing the offending subheading.
2. **PandocMissing** in notebooks — see "pandoc on PATH" entry below.

### RST heading-style hierarchy is positional, not character-based

**Symptom**: After adding a `~~~` subheading inside a `==`/`--` file,
subsequent `--` sections in the same file are reported as
"skip from level 2 to 4" ERRORs.

**Cause**: Sphinx assigns RST heading levels by the **order each underline
character first appears** in the document, not by the character itself.
Introducing `~~~` between existing `==` and `--` shifts `--`'s level from 2
to 3 globally, breaking any subsequent section that was already nested at
level 2.

**Fix**: don't introduce new heading characters mid-document. If you need a
sub-emphasis, use a `**bold inline marker:**` paragraph instead of a new
heading underline.

### `nbsphinx` needs pandoc on PATH for parent AND worker subprocesses

**Symptom**:
- Local docs build fails with `nbsphinx.NotebookError: PandocMissing`
- Or only fails when running with `--jobs auto` (works with `--jobs 1`)

**Cause**: nbsphinx invokes pandoc via `pypandoc`, which looks for `pandoc`
binary on PATH. With parallel workers, each subprocess inherits PATH but loses
custom additions that weren't exported.

**Fix** (sandbox without `apt-get`):
```bash
uv pip install --python .tox/docs/bin/python pypandoc_binary
mkdir -p /tmp/pandoc-bin
ln -sf "$(realpath .tox/docs/lib/python3.12/site-packages/pypandoc/files/pandoc)" \
       /tmp/pandoc-bin/pandoc
export PATH="/tmp/pandoc-bin:$PATH"
```

**Fix** (real CI): `apt-get install -y pandoc` in `.github/workflows/docs.yml`.

### tox `set_env` doesn't pass through tox-uv reliably

**Symptom**: `[tool.tox.env_run_base]` has `set_env = { LC_ALL = "en_US.utf-8" }`
but the docs env crashes with `locale.Error: unsupported locale setting` on
systems that don't have en_US.UTF-8 generated.

**Cause**: The locale is set, but the *generated* locale isn't present on a
clean Ubuntu or sandboxed Linux. `locale.setlocale(LC_ALL, '')` fails when
`LC_ALL` points at an ungenerated locale.

**Fix** (local): `sudo locale-gen en_US.UTF-8`, or `LC_ALL=C.UTF-8` (always available).
**Fix** (CI): real GitHub runners have en_US.UTF-8 by default — local-dev only.

### `grid-item-card` needs a parent `.. grid::`

**Symptom**: sphinx-design WARNING: "The parent of a 'grid-item' should be a 'grid-row'".

**Cause**: A standalone `.. grid-item-card::` without a parent `.. grid::` is invalid.

**Fix**: wrap even single cards in a grid:
```rst
.. grid:: 1
   :gutter: 2

   .. grid-item-card:: My standalone card
      ...
```

### Sphinx autosummary side-effects on local builds — do NOT commit

**Symptom**: After running `sphinx-build` locally, `git status` shows
modifications to `docs/apidocs/qiskit_metal.renderers.PlotCanvas.rst` and
possibly two new files at `docs/` root
(`qiskit_metal.analyses.em.cpw_calculations.rst`,
`qiskit_metal.analyses.quantization.lumped_capacitive.rst`).

**Cause**: `sphinx.ext.autosummary` regenerates `.rst` stubs on each build,
and the content depends on what modules are actually importable at the time.
With heavies mocked, fewer methods are discovered (→ 376-line removal in
PlotCanvas.rst). With autosummary walking different module sets, new stubs
appear at docs/ root.

**Fix**: don't commit these — they're build artifacts. Either:
- Run `git checkout HEAD -- docs/apidocs/` before pushing, or
- Add the new docs/ root stubs to `.gitignore` (currently they aren't), or
- Configure autosummary to write to a build-only directory

### Pre-existing "MetalGUI docstring indentation" ERROR

**Symptom**: Build log has `_gui/main_window.py:docstring of qiskit_metal._gui.main_window.MetalGUI:11: ERROR: Unexpected indentation. [docutils]`

**Cause**: Docstring uses indentation that docutils interprets as a block
quote, then sees content that breaks the assumed indentation level.

**Status**: Non-fatal warning, present since at least v0.6.x. Queued for a
separate `_gui` docstring cleanup pass.

### v0.6.3 docs band-aid → v0.7.0 proper fix recap

**v0.6.3** wrapped the `is_building_docs()` import block in
`renderers/__init__.py` in `try/except (ImportError, OSError)` and emitted an
`ImportWarning`. This let docs CI keep working even when the runner lacked
native libs.

**v0.7.0** replaced this band-aid with the proper architecture:
1. Docs tox env installs lite only (`extras = []`)
2. `conf.py` pre-mocks heavies in `sys.modules` before `import qiskit_metal`
3. `autodoc_mock_imports` catches anything the pre-mock missed
4. `renderers/__init__.py` returns to plain imports

The `try/except` and the `warnings` import in `renderers/__init__.py` were removed.

### Quick docs-build sanity script

When in doubt, this reproduces the CI environment locally:

```bash
rm -rf .tox/docs
uv pip install --python .tox/docs/bin/python pypandoc_binary  # if not in CI
LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
  PATH="/tmp/pandoc-bin:$PATH" \
  uvx --with tox-uv tox -e docs
# Exit code 0 = green; exit code 2 = look for ERROR: lines in the log
```

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

## MetalGUI segfaults — the whole story lives in one document

Issue #1048 and its descendants (#1103, #1109) produced four distinct
crash bugs, five releases of fixes, and a set of defenses in
`_gui/` that look like removable defensive noise and are not.

That history is written up in
**`docs/architecture/gui_crash_defenses.md`** — read it before
touching GUI startup, teardown, stylesheet handling, or persisted
window state.

The two lessons that generalize beyond the GUI:

**CI passing is not evidence there.** The Windows `show()` crash never
reproduced under Xvfb or on GitHub runners, because runners start with
an empty registry — which is exactly the state that works. Reporter
confirmation on the affected hardware was the only real signal.

**A defense can be load-bearing by accident.** The stylesheet was
loaded at the end of `restore_window_settings`, after five guards that
`clear()` and return early. That looked like a bug — and is one, the
theme is genuinely skipped on a fresh profile. But moving the load out
so it always runs turned `test_gui_init.py` and `test_gui_teardown.py`
from 5 passed to 5 failed with `SIGBUS` (attempted 2026-08-07,
reverted). The early returns were accidentally protecting a known
crash trigger. Before "fixing" something that looks vestigial in a
crash-hardened path, check what it is standing in front of.

**"Internal C++ object already deleted" is never noise** (2026-08-10,
PR #1180). One appeared after the full suite already reported passing,
exit code 0, and got classified as a benign at-exit artifact and
documented as cosmetic. CI then produced `-11` segfaults on the macOS
matrix and self-heal failures on the display jobs from the same leak
class: deferred Qt callbacks (naked `QTimer.singleShot(ms,
bound_method)`, model poll timers) outliving the widgets they touch.
The Python-visible RuntimeError and the native segfault are the same
use-after-free; which one you get depends only on whether the freed
memory was reused yet. Treat any such message anywhere in output as a
live crash report. `tests/test_gui_lifecycle_stress.py` fails on them;
`single_shot()` in `_gui/utility/_toolbox_qt.py` is the required
pattern for delayed calls.

**A crash marker must open before the code it guards, on a medium a
crash can't lose.** The `restore_in_progress` QSettings cookie failed
in CI two ways at once: it was set partway through init, so crashes
before that point left no cookie ("crashed but did not leave the
cookie set"), and `QSettings.sync()` routes through `cfprefsd` on
macOS, which flushes asynchronously — a native crash right after
`sync()` can lose the very write meant to record it. Replaced by the
startup journal (`_gui/startup_journal.py`): a plain flag file,
fsync'd, written as the first Python instruction of
`MetalGUI.__init__`. If a guard's coverage window opens after any
guarded code runs, or its persistence isn't a real disk barrier, it
will eventually miss exactly the crash it exists for.

**Full-GUI lifecycle tests belong in subprocesses.** Two separate CI
rounds died the same way: an in-process test that constructs a real
MetalGUI (first the stress test, then the click-and-arrow test) lost
the nondeterministic teardown race on a slow runner and the segfault
killed the whole pytest process, cancelling the rest of the matrix.
Marker-based subprocess isolation keeps the contract strict while
containing the blast. Corollary for QTest synthetic clicks: matplotlib
transforms are physical pixels, Qt wants logical -- divide by
``devicePixelRatioF()`` or clicks silently miss on Retina while
passing on CI's ratio-1 runners.

**Headless-local passing says nothing about the on-screen crash
class.** Offscreen never executes the paint/QPA paths where these
crashes live, and one fast local run rarely samples a race that 11
slow CI jobs sample every push. The pre-push hook now runs
`test_gui_init.py` + `test_gui_teardown.py` on the real display
whenever a push touches `_gui/` or `renderer_mpl/` (~40s) — the local
gate that would have caught the PR #1180 matrix failures before push.

## Component-authoring traps (silent, geometric, no traceback)

These bit while building a real chip from published images. What they
share is that nothing raises — the geometry is simply wrong, and it
looks plausible until you measure it.

**`add_pin`'s two input forms fail quietly.** With the default
`input_as_norm=False`, `points` is the line **across** the conductor
(the pin's face): `middle` is that line's midpoint and `normal` comes
out perpendicular. With `input_as_norm=True`, `points` is a line
**along** the connection: `middle` is `points[1]` and `normal` runs
toward it. Hand a route's first segment to the default form and the pin
lands at the *midpoint of the segment* with a normal rotated 90°, and
nothing complains. `LaunchpadWirebond`'s `tie` pin is the reference for
an end-of-trace pin. Assert on `pins[name]['middle']` and `['normal']`
in a test — don't trust the call.

**A component's rotation option is not necessarily its pin's angle.**
`StarQubit.rotation_*` sits 90° ahead of where the corresponding pin
ends up: `rotation_rdout='45'` puts `pin_rdout` at 315. This silently
rotated every readout arm on a 17-qubit reproduction for several
passes, because the four *coupler* arms at 0/90/180/270 map onto the
same set when shifted by −90 and so looked fine. Any component taking
an angle should state in its docstring where the resulting **pin**
lands; several still don't.

**Verify the built geometry, never the options you passed.** Both of
the above are invisible to a check that reads back `component.options`
— that only confirms you passed what you meant to pass. Read the pin
normals (or the qgeometry) back out of the design and assert on those.
That is the only check that catches this whole class.

**`QRoute.connect_simple()` cannot express non-Manhattan paths.** It
tries four fixed shapes (`^|_`, `^^|`, `__|`, `_|^`) between
consecutive waypoints and raises `QiskitMetalDesignError` when none
fits. On a real device's octilinear control lines (measured: 55%
axis-aligned, 41% at 45°) it failed outright on 7 of 17 routes and
turned the rest into staircases. When the path is already known,
`PolylineCPW` (`qlibrary/tlines/polyline_cpw.py`) draws it as given —
that is a different job from routing, which is why it is a plain
`QComponent` and not a `QRoute`.

**The DRC needs no per-component configuration — but it does need you
to model two things.** The rules read qgeometry generically, so any
component you write is covered automatically. What it cannot infer:

* *Intent to connect.* A component wired up without going through the
  `pin_inputs` machinery reports its intended junctions as metal-overlap
  shorts. `MetalOverlapRule` skips pairs sharing a net, so call
  `design.connect_pins(...)` — six spurious findings vanished at once.
  For a joint in the middle of a line, add a `PolylineCPW` tap and
  connect to that.
* *Out-of-plane structure.* Overlap and spacing are grouped **per
  layer**, so a crossover modelled properly — base trace interrupted,
  span on `Airbridge`'s bridge layer — simply is not an overlap. Drawing
  both conductors on layer 1 and then arguing the finding is expected is
  the wrong fix; putting the span on its own layer is the right one, and
  it drops the report to zero errors without touching a rule.

`validate(design, rules=...)` lets you swap or retune rules, but there is
no waiver mechanism for "expected" findings — if you need one, say so
rather than quietly widening a threshold.

**An unconnected CPW end is a short, not an open.** Path metal and its
ground cut end flush (flat caps in the renderers and the DRC; gdstk
`FlexPath` defaults to flush ends in GDS), so a bare line end butts the
ground plane. On a 17-qubit reproduction all 17 capacitively coupled drive
lines were drawn this way and would have fabricated shorted. Terminate every
end explicitly (`OpenToGround` / `ShortToGround`) or connect it;
`DanglingEndRule` (in `SHAPE_RULES`) reports the ones you missed.

**A line cut for an `Airbridge` is broken unless the bridge is wired.**
Splitting a line at a crossing and placing an `Airbridge` over the gap
leaves two unconnected ends — each a short, per the entry above — unless
the cut ends are connected to the bridge's pins `a`/`b`. Sixty such ends
passed every default rule on the same chip.

**Mid-line branches: use `PolylineCPW` taps, not waivers.** A stub joined
to the middle of a line has no pin to connect, so the DRC reports the joint
as a metal-overlap short. A `taps={name: [x, y]}` pin on the line makes the
joint a real net; a per-joint `Waiver` works but records an exception for
ordinary connectivity.

**Editing a CRLF file can rewrite every line.** Some files here are CRLF
(`qlibrary/__init__.py`); an editor or tool that writes LF turns a two-line
change into a whole-file diff, and `git diff --stat` shows only a large
count. Check `git diff --ignore-cr-at-eol --stat` against the plain stat
before committing, and write CRLF files back as bytes.

**Check the thumbnail and the docstring after adding a component.** The
generator used to frame against the die outline (small parts rendered as
specks) and to prepend the `.. image::` directive (making it the docstring's
summary line). Both are fixed in `_dev/generate_qlibrary_thumbnails.py`;
still look at the PNG and the class docstring it produced.

### A sawtooth of spikes along a straight CPW is the drawing, not the design

`QMplRenderer._calc_fillet` computed the corner angle with
`arccos(dot(u1, u2))`. On a resampled straight run the dot product rounds to
-1.0000000000000002, arccos returns NaN, NaN passes every "can this corner be
filleted" check, and the fillet points come out NaN -- drawn (GUI and
`qm.view`) as regular V-shaped spikes along the line. 43 of 164 lines on the
17-qubit chip were affected; the stored geometry was fine. Clip the dot
product and treat near-straight corners as straight
(`tests/test_mpl_fillet.py`). When a drawn line looks wrong, compare the
drawn polyline with the stored one before touching the design.

### Match a component's internal layout to a close-up before placing it

The 17-qubit rebuild put every StarQubit's four coupler arms on the compass
points because the lattice runs that way. The device qubit (a close-up in
the slides) has five pads about 72 degrees apart, with the SQUID on the
island arm between the readout pad and a coupler pad. Forcing the arms to
90 degrees produced three separate-looking symptoms -- couplers leaving
their pads sideways, a junction drawn on top of a coupler pad (island
shorted to it), and floating island slivers between the 45-degree-apart
cuts -- each of which got its own workaround before the cause was found.
Measure the element's own geometry (pad angles, where the junction sits)
from a close-up first; the traced lines then meet the pins square-on without
special cases.

### A clean DRC after a change that should not have fixed anything

When the pads moved, the ground-continuity warning disappeared although the
plaquette ground islands were still there: nanometer-wide slivers left by
floating-point booleans where two etched edges almost coincide joined them
to the main ground. The rule now ignores links narrower than
`min_link_width` (0.1 um). If a check stops firing and you cannot say why,
find out before believing it.

### GDS export silently dropped whole line gaps ("Unable to link hole")

The ground plane was one `gdstk.boolean(chip, all_cuts, "not")`. The result
is a polygon with every enclosed cut as a hole; when gdstk cannot link a hole
to the outline it prints `[GDSTK] Unable to link hole in boolean operation`
to stderr and *drops the hole*. On the 17-qubit chip three whole flux-line
gaps came out as solid ground -- DRC was clean, the file was wrong, and a
harmless-looking 40 um change elsewhere was enough to trigger it. Fixed by
`renderer_gds/gds_boolean.subtract_in_strips` (ground and cheesing): strips, then each
strip checked against shapely by area and rebuilt without holes if gdstk got it wrong --
strips alone were not enough once the qubit geometry changed.
If you see that message, check the GDS, not the design. Side effect worth
knowing: cheesing against strip-sliced ground went from ~40 s to ~1 s.

### `rebuild()` used to drop connections made with `design.connect_pins`

`QComponent.rebuild` deletes the component's nets before `make()`. Routes
reconnect inside `make()`, so nobody noticed; anything wired with
`design.connect_pins` (terminations, capacitors, airbridges, `PolylineCPW`)
silently lost its connection on any rebuild — including `design.rebuild()` and
GUI edits — and the partner pin kept a stale `net_id`. On the 17-qubit chip one
`design.rebuild()` took the net table from 656 rows to 0 and DRC from clean to
126 overlap errors. Fixed: `rebuild` records the partners and restores those
`make()` did not reconnect (`tests/test_rebuild_connections.py`). When a design
is DRC-clean after building but not after a rebuild, check `design.net_info`
first.

## LOM 2.0 and scqubits: the lockfile hides what a fresh install gets

`CompositeSystem.hamiltonian_results` had no test, and it broke in two
different ways depending on the resolver:

- **macOS:** scqubits 4.2+ pins `scipy<=1.13.1` on darwin/py>=3.10, so a
  resolver that keeps a newer scipy picks scqubits 4.1.0, which uses
  `np.float_` (gone in numpy 2).
- **Linux / fresh pip:** scqubits 4.3.1 with qutip 5.3 fails inside scqubits
  itself (`Unsupported operator type: csc_array`), because qutip 5.3 returns
  scipy sparse arrays. `uv.lock` pinned qutip 5.2.2, so the repo venv never
  saw it.

`analyses/quantization/_scqubits_compat.py` handles both. To check a
dependency combination the lock does not produce, build a scratch venv
(`uv venv` + `uv pip install -e . "scqubits==X" "qutip==Y"`) and run
`tests/test_lom_core_hamiltonian.py` there; the repo's pytest config needs
`-p no:rich -o addopts=""` without the dev extras.

## Open FEM: gmsh + scikit-fem

From the solver behind tutorials 4.41–4.45
(`docs/tut/resources/package_modes/`). Design and physics notes:
`docs/architecture/open_fem_scikit_fem.md`.

### gmsh 1D meshing takes minutes with a `Min` of two size fields

**Symptom**: meshing a 30 mm box with 200 paddles goes from ~3 s to
~400 s after adding a second `Threshold` field (junction seeding)
combined with `Min`; almost all of it in "Meshing 1D".

**Cause**: with a background field, gmsh integrates 1/size along each
curve to place nodes, to `Mesh.LcIntegrationPrecision` (default 1e-9).
The `Min` of two distance fields makes that integration crawl.

**Fix**: `gmsh.option.setNumber("Mesh.LcIntegrationPrecision", 1e-3)`
— same mesh, 1D in ~1 s. Merge curves into one `Distance` field when
they share a size.

### `basis.interpolator` / `basis.probes` stall on large tetrahedral meshes

**Symptom**: evaluating a scikit-fem field at 100 points on a
~100k-element mesh runs for minutes; a notebook kernel doing a 200×200
field map appears to die.

**Cause**: the generic element finder is not built for many queries on
big meshes.

**Fix**: locate points with a `scipy.spatial.cKDTree` over element
centroids plus barycentric coordinates, and evaluate the shape
functions directly (Whitney functions for `ElementTetN0`, Lagrange for
P2). 40k points in ~0.4 s, identical to the interpolator to 1e-16.
`package_modes._Locator`.

### ARPACK shift-invert on a curl-curl problem is 100× slower than it should be

**Symptom**: `eigsh(K, M=M, sigma=s, k=3)` on 27k unknowns takes
~100 s; the two extra eigenvalues come back as 0.

**Cause**: the curl-curl operator has a huge null space (gradients,
including static charge states of floating conductors). Asking for
more eigenvalues than lie near the shift makes ARPACK resolve that
degenerate cluster.

**Fix**: request only the modes near the shift (`k=1`/`2`), and pass
your own `OPinv` from one factorization.

### SuperLU fill on 3D edge-element matrices

**Symptom**: `splu` with the default `COLAMD` needs 100M+ nonzeros and
tens of seconds at 70k unknowns.

**Fix**: symmetric permutation from `pymetis.nested_dissection`, then
`splu(..., permc_spec="NATURAL", options=dict(SymmetricMode=True),
diag_pivot_thresh=0)`: ~4× less fill and time. Without pymetis,
`permc_spec="MMD_AT_PLUS_A"` is the next best.

### gmsh `fragment` with no tool entities returns an empty map

**Symptom**: meshing an empty box (no paddles) gives no tetrahedra
material tags → `np.vstack` of an empty list.

**Fix**: classify volumes after `fragment` by bounding box (below the
slab top = substrate), not through the fragment output map.

### A mesh slice through mesh nodes has holes

**Symptom**: cutting tetrahedra with a plane that passes exactly
through nodes (e.g. along a junction line) leaves white gaps.

**Fix**: offset the plane slightly (1.51 mm instead of 1.5 mm).

### gmsh on Colab: `OSError: libGLU.so.1: cannot open shared object file`

**Symptom**: after `pip install "quantum-metal[skfem]"` (or `[mesh]`) on
Google Colab, the first gmsh call fails with `libGLU.so.1` missing.

**Cause**: the PyPI gmsh wheel is built with its GUI and links against
system libraries pip cannot install. For gmsh 4.15.2 (`libgmsh.so`,
`DT_NEEDED`): libGLU, libGL, libX11, libXext, libXrender, libXcursor,
libXfixes, libXft, libXinerama, libfontconfig, libgomp. Colab's image lacks
at least libGLU.

**Fix**: in the notebook's Colab install cell, before pip:
`!apt-get -qq update && apt-get -qq install -y libglu1-mesa libgl1
libxcursor1 libxft2 libxinerama1 libxfixes3 libxrender1 libxext6
libfontconfig1` (packages already present are no-ops). Tutorials 4.41–4.45
and 54 carry it.

### The impedance fit finds one pole where there are two

**Symptom**: `fit_impedance` raises "found 1 of 2 poles" for a weakly
coupled qubit, or for a port shunted by 1 pH.

**Cause**: the pole and the zero next to it fall inside one frequency
step, so `det X` shows no sign change.

**Fix**: sample adaptively around the poles (a reduced model gives
them), never exactly on a pole; keep the residual vector a fixed length
when samples near a trial pole are excluded (least squares
finite-differences it).

## Executing notebooks that open MetalGUI: the kernel can hang

`metal.gui(design)` in a Jupyter kernel switches the kernel's event loop to
ipykernel's `loop_qt` during that cell (`get_ipython().kernel.eventloop` is
`None` before, `loop_qt` after). When a runner (nbclient, the
`notebooks-qt-refresh` job) sends the next execute request immediately, the
request can arrive before ipykernel's Qt socket notifier is armed; the kernel
then idles in `QEventLoop.exec()` and never runs the cell. Seen in about 1 of
3 runs of a notebook with a GUI (ipykernel 7.1, PySide6 6.10, macOS,
`QT_QPA_PLATFORM=offscreen`); never when cells are run by hand. A native
stack (`sample <pid>` on macOS) shows the main thread in
`QEventLoop::exec` / `qt_safe_poll` at 0% CPU. Use a per-cell timeout
(a few minutes) and retry the notebook; the outputs of the run that
completes are fine. At kernel shutdown ipykernel's Qt hook can also print
`OSError: Stream is closed`; that is ipykernel tearing down, not Metal.

`gui.screenshot()` also writes `shot.png` and `shot750.png` into the working
folder; clean them up after executing a notebook.

## What this list doesn't include

Stuff that's NOT a "lesson learned" — those go in
`.claude/context/architecture.md` (how things are structured) or
`.claude/context/ecosystem.md` (why things are the way they are).
This file is **specifically things that bit us in production**.

When you fix a real bug, add an entry here. Future agents will
thank you.
