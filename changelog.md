# Changelog Note Scratchpad for Developers

This log is used by developers to jot notes.

For the offical user-facing changelog for a particular release can be found in the correspondent Github release page. For example, you can find the changelog for the `0.0.4` release [here](https://github.com/Qiskit/qiskit-metal/releases/tag/0.0.4)

The changelog for all releases can be found in the release page: [![Releases](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)

## Quantum Metal v0.6.2 (deprecation-notice release)

**Pre-flip release.** All v0.6.x install behaviour is unchanged
— but a `FutureWarning` now fires on `import qiskit_metal` letting
users know v0.7.0 will move the heavy dependencies (PySide6,
qdarkstyle, pyaedt, pyEPR-quantum, gmsh) out of base into opt-in
extras. To preserve current behaviour, install with
`pip install 'quantum-metal[full]'` before upgrading to v0.7.0.

This release also lazifies the last remaining eager heavy-dep
import — gmsh — so the `tests-lite` CI matrix can validate the
full v0.7.0 install behaviour ahead of the actual deps flip.

### What landed

- **gmsh lazification** in `renderer_gmsh/gmsh_utils.py` and
  `renderer_gmsh/gmsh_renderer.py`: same `try/except` +
  `_require_gmsh()` pattern as the pyEPR/pyaedt lazification in
  v0.6.x. `QGmshRenderer.__init__` raises a clear
  `ImportError: ... pip install 'quantum-metal[fem]'` when gmsh
  isn't available. The `_start_renderers` skip-and-log path
  catches it.
- **gmsh version pin tighten**: `gmsh>=4.11.1` → `gmsh>=4.15.0,<5`.
  The dev env already ships gmsh 4.15.0 (bumped in v0.5.3.post1
  but the floor wasn't updated). Upper bound caps before any
  future gmsh 5 lands.
- **`FutureWarning` on `import qiskit_metal`** advertising the
  v0.7.0 lite-flip. Fires once per process via Python's standard
  warning deduplication. Suppress with
  `QISKIT_METAL_SUPPRESS_LITE_FLIP_WARNING=1`.
- **Version bumped** to 0.6.2.

### Nothing else changed

- Public API: unchanged
- Test behaviour: unchanged (all 458 tests still pass)
- Install behaviour: unchanged (heavies still in base)
- Headless / lite paths: unchanged

The next release (v0.7.0) will flip `pyproject.toml`'s base
dependencies and the warning becomes truth.

## Quantum Metal v0.7.0 (Unreleased — planned)

**Headline: lite-by-default install.** This release moves the heavy
optional dependencies (`pyside6`, `qdarkstyle`, `pyaedt`,
`pyEPR-quantum`, `gmsh`) out of `[project.dependencies]` and into
extras. `pip install quantum-metal` becomes the small,
orchestration-friendly base install; the GUI / Ansys / FEM stacks
are opt-in.

See [ROADMAP.md](./ROADMAP.md) and
[`docs/migration-to-v0.7.0.rst`](./docs/migration-to-v0.7.0.rst) for
the full picture.

### Breaking changes — read this if you upgrade

- `pip install quantum-metal` no longer pulls PySide6, AEDT, gmsh,
  pyEPR, or qdarkstyle. If you used `MetalGUI` or any HFSS/Q3D /
  gmsh / pyEPR-EPR code path, run one of:
  - `pip install quantum-metal[full]` — restore the v0.6.x
    all-batteries-included experience
  - `pip install quantum-metal[gui]` — just MetalGUI + qdarkstyle
    + PySide6
  - `pip install quantum-metal[ansys]` — just AEDT/pyEPR (the EPR
    analysis code paths and the HFSS/Q3D renderers)
  - `pip install quantum-metal[fem]` — just gmsh (mesher for the
    Elmer / Palace path)

### Why

- AI orchestration loops, Colab / Binder, cloud Jupyter, headless
  CI, and any non-interactive workflow no longer have to install or
  ignore hundreds of MB of Qt + AEDT they'll never use.
- Designs build, render to GDS, view inline (via `qm.view(design)`),
  and feed downstream solvers with a base install of a few dozen MB
  instead of ~1 GB.

### What didn't change

- `import qiskit_metal` (the package name stays for backward
  compatibility through the v0.6.x / v0.7.x line)
- Public API on `QDesign`, `QComponent`, `QRenderer`
- Tutorial notebooks (the analysis ones need the relevant extras to
  run; this is now spelled out in each notebook's install cell)

### In-flight as of this entry

- pyEPR-in-analyses: lazified (PR #1074, landed)
- Wirebond E712 audit note recorded in lessons-learned (PR #1073)
- gmsh-in-renderer_gmsh: lazification PR pending
- pyEPR/pyaedt-in-renderer_ansys*: lazification PR pending — these
  live in the hard-touch HFSS zones, separate PR for review care
- The actual `pyproject.toml` deps flip (the user-visible change):
  blocked on the lazification PRs landing first

### Deprecation path

A v0.6.2 release before v0.7.0 will ship a
`DeprecationWarning` on `import qiskit_metal` if it detects an
"installed but won't be in v0.7.0 base" set, pointing users at
`quantum-metal[full]` for a no-op migration.

## Quantum Metal v0.6.1 (May 2026)

Patch release after the v0.6.0 tag-only failure (PyPI publish step
failed during the v0.6.0 cut; `pip install quantum-metal==0.6.0`
404s. Don't tag-and-walk-away on releases — verify PyPI received
the wheel before announcing). See `.claude/commands/release.md`
post-mortem.

User-visible changes vs v0.6.0:

- Sphinx docs build warnings resolved
- Tutorial notebook heading-level hierarchy normalized (nbsphinx
  was choking on `# → ###` skips)
- qutip 5 + pyEPR 0.9.5+ version sync — fixes `np.array([Qobj])`
  stacking issue, `np.absolute(Qobj)` issue, and the HFSS 2024.1+
  solution-type rename
- Ruff auto-fixes + trailing-whitespace cleanup

## Quantum Metal v0.6.0 (May 2026)

**Major release.** Foundation for the lite-by-default flip in
v0.7.0. All changes here are additive — current users on v0.5.x
upgrade without code changes.

### Highlights

- **`qm.view(design)`** — standalone matplotlib viewer that works
  without PySide6 / Qt installed. Renders in a Jupyter notebook
  inline or to a file. The headless entry point for tutorials,
  CI, agent workflows, and any environment where you don't want
  to install a Qt binding. See `docs/headless-usage.rst`.
- **Lazy Qt initialization** — `import qiskit_metal` no longer
  requires PySide6 at module-load time. Set
  `QISKIT_METAL_HEADLESS=1` to skip the Qt-backend probe entirely;
  `MetalGUI` still works on full installs.
- **`[gui]` / `[ansys]` / `[fem]` / `[full]` optional-dependency
  extras** added to `pyproject.toml`. In v0.6.x they're
  informational (every extra's deps are also in base), but the
  `tests-lite` CI job exercises the lite-install path so it stays
  green for v0.7.0's flip.
- **`tests-lite` CI matrix entry** — runs the full test suite on
  a venv built without PySide6 / pyaedt / gmsh, catching any
  regression on the lite path.
- **`qutip 5` + `pyEPR 0.9.5+` compatibility** — fixes
  `np.array([Qobj])` no longer stacking, `np.absolute(Qobj)` no
  longer working directly, and the HFSS 2024.1+
  `solution_type` rename (`"DrivenModal"` →
  `"HFSS Modal Network"`).
- **Pandas 2.2 compatibility** — uses `.iloc[]` for positional
  indexing where 2.2 stopped doing the old positional-fallback.
- **Type annotations** on the core public API methods of
  `QComponent`, `QDesign`, and the renderer bases — unlocks
  downstream type-checking for orchestration tools.

### New tests

- `test_pin_normals_point_outward` — static sanity check that
  every component's pins point away from the component centroid.
  Catches HFSS port-flip bugs at component-author time, not at
  HFSS-eval time. One known failing case logged:
  `LaunchpadWirebondDriven.in` (see `KNOWN_INWARD_PINS`).
- Static AST audit that every `self.options.X` access has a
  matching key in `default_options`. Catches typos that would
  silently fall through.
- `test_view_hides_layers` — gates the new `qm.view(design)`
  `hidden_layers={...}` parameter.

### Tutorials

- Every tutorial notebook now has a "no Qt required" callout
  near the top, explaining when the tutorial does and doesn't
  need `MetalGUI`.
- New `1.4 Headless Quick View.ipynb` — short notebook showing
  the `qm.view(design)` path end-to-end with no Qt.
- The headless tutorial path is exercised in CI via
  `nbconvert --execute` on `1.4 Headless Quick View.ipynb`
  inside the `tests-lite` job.

### Infrastructure

- `CLAUDE.md` + `.claude/` directory: documents the repo's
  hard-touch zones, recurring tasks, and lessons-learned for
  future AI agents.
- `tests-lite` uses `.venv/bin/python` directly (not `uv run`)
  because `uv run` was re-syncing the venv and overwriting the
  custom lite-install state. See
  `.claude/context/lessons-learned.md`.

### Known issues

- `LaunchpadWirebondDriven.in` pin normal points inward (HFSS
  validation blocked the fix in v0.6.0; documented in
  `tests/test_qlibrary_pin_sanity.py::KNOWN_INWARD_PINS`).
- 13 ruff findings in HFSS / `_gui/` deferred to v0.6.1+ for
  validation environment. (**Resolved** in v0.6.1+ via the
  ruff-sweep PR #1070, with one caveat documented in
  `.claude/context/lessons-learned.md`.)
- v0.6.0 PyPI publish failed; install
  `quantum-metal>=0.6.1` instead. (**Fixed** in v0.6.1.)

## Quantum Metal v0.5.3.post1 (Jan 23, 2026)
- Pinned pyaedt to less than v0.24 due to bugs. 
- Updated gmsh dependency 4.11.1 → 4.15.0

## Quantum Metal v0.5.3 (Jan 17, 2026)

- Various dependency updates. 
- Removed descartes and cython dependencies (unused).
- pandas, geopandas, scqubits and qutip updates to latest major version. Should fix [#1027](Ihttps://github.com/qiskit-community/qiskit-metal/issues/1027).
- Updates to contributor guide to fix inconsistent headline levels. Also convert example images to rst source code blocks. 
- Update various parts in the docs to indicate near-term versioning updates. 
- Update uv version to 0.9.24 in CI. Remove step to upgrade runner packages in CI for workflows speedup. 
- Convert package from [flat layout to src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/#src-layout-vs-flat-layout). This is a forward looking change that will help decouple source code from docs and tests. In this configurations, the any package code must be imported using the package name, instead of relative imports as before. This also requires installing the package in the virtual environment (either as editable or via the wheel) to import it, which we already support in our uv-based workflows. 
- Fixed floating `QLabel` bug in `MetalGUI` [#1031](https://github.com/qiskit-community/qiskit-metal/issues/1031).
- New CI workflow to bump version using uv, commit and push a git tag and create a draft release. This also triggers the PyPI release. 
- Update CI workflows to use Python 3.12.


## Quantum Metal v0.5.2 (Dec 11, 2025)

- We have adopted uv as a project/dependency management tool. 
- Tasks are still run using tox, but with the tox-uv plugin. 
- We adopted ruff for linting and formatting. We have a good starting configuration for linting, but it needs some work before it could be considered stable. 
- The GitHub actions workflows have been updates with these changes. 
    - Python 3.12 is the slowest to build wheels in CI, partly because qutip and pandas take a very long time to build on this version. This needs to be investigated. 
- New developer onboarding instuctions added to `README_developers.md`. The old instructions in`README_developers.md` have been retained with a note for usage on older versions of `qiskit-metal`. 
- Development install instructions have been added to documentation in the "Contributor Guide". 
- Installation instructions have been updates. More updates to come. 
- Single source package version from `pyproject.toml`.
- Updated to contributor docs to add instructions on bumping package version using uv. 



## QISKIT METAL v0.5 (2025)

### Major Updates

This release addresses significant package changes and ports:

- **PyQt5 to PySide6**: A complete overhaul of the GUI.
- **GDSPY to GDSTK**: Replaced GDSPY with the more robust GDSTK library.
- **PYAEDT to Ansys (v1.0)**: Major update with a new syntax. Extensive testing required.
- **Installation Improvements**: Transitioned to `venv` for faster environment setup, moving away from `conda`. Also, most package versions have been floated and upgraded.
- **Docs**:
    - Migrate qiskit_sphinx_theme to the new theme
    - Add divs on the front page to tuts etc
    - Add user content and showcase page

---

### GUI Enhancements

1. **Traceback Reporting**: Added detailed traceback reporting in the logging system to aid debugging.
2. **Model Reset Issue**: Fixed the issue causing the warning: *"metal: WARNING: endResetModel called on LibraryFileProxyModel(0x17fda8200) without calling beginResetModel first (No context available from Qt)"*.
3. **MPL Renderer Issue**: Resolved the error: *"Ignoring fixed y limits to fulfill fixed data aspect with adjustable data limits. Ignoring fixed x limits to fulfill fixed data aspect with adjustable data limits."*.
4. **UI Button Update**: Added a red border style to the "Create Component" button in the UI for better visibility.

---

### PYAEDT Update

- **FutureWarning**: The `pyaedt` module has been restructured and is now an alias for the new package structure based on `ansys.aedt.core`. To avoid issues in future versions, please update your imports to use the new architecture. Additionally, several files have been renamed to follow the PEP 8 naming conventions. For more information, refer to the [Ansys AEDT documentation](https://aedt.docs.pyansys.com/version/stable/release_1_0.html).
