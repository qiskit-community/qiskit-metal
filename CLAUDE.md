# CLAUDE.md — Quantum Metal repo guide for AI agents

> If you are a Claude (or other AI agent) opening this repo for the first
> time, **read this file end-to-end before touching anything**. It points
> at the rest of the context that will save you hours.

## What this repo is

**Quantum Metal** (formerly Qiskit Metal) is an open-source Python framework
for designing and analysing superconducting quantum chips. The PyPI package
is `quantum-metal`; the import path is still `qiskit_metal` for backward
compatibility. The community-maintained successor to IBM's original
Qiskit Metal — the rebrand is in progress through the v0.6.x line.

Stack: Python 3.10–3.12 · `shapely` for geometry · `geopandas` /
`pandas` for storage · `matplotlib` for headless viewing · `PySide6` for
the optional desktop GUI · `pyEPR-quantum` / `pyaedt` / `gmsh` /
`Elmer` for analysis backends.

## Architecture map (skim these first)

| Path | What lives there |
|------|------------------|
| `src/qiskit_metal/qlibrary/` | All `QComponent` subclasses (transmons, terminations, lumped, couplers, routes, sample shapes). The user-visible catalogue. |
| `src/qiskit_metal/qlibrary/core/base.py` | `QComponent` — the load-bearing base class. Read end-to-end before touching any component. |
| `src/qiskit_metal/designs/` | `QDesign` and subclasses (`DesignPlanar`, `DesignFlipChip`, ...). Components attach to a design. |
| `src/qiskit_metal/renderers/renderer_base/` | `QRenderer` and `QRendererAnalysis` — the two abstract bases. See `docs/architecture/renderer_protocol.md`. |
| `src/qiskit_metal/renderers/renderer_ansys/` | Legacy COM-based HFSS/Q3D renderer. Hard-touch zone. |
| `src/qiskit_metal/renderers/renderer_ansys_pyaedt/` | New pyaedt-based HFSS/Q3D renderer. Migration in progress. |
| `src/qiskit_metal/renderers/renderer_gds/` | `QGDSRenderer` — export to GDS. Pure-Python; safe to touch. |
| `src/qiskit_metal/renderers/renderer_mpl/` | The matplotlib renderer used by both the Qt GUI and `qm.view`. `QMplRenderer` no longer requires Qt as of v0.6.1. |
| `src/qiskit_metal/renderers/renderer_gmsh/`, `renderer_elmer/` | Open-source FEM path. Depends on `gmsh` (optional). |
| `src/qiskit_metal/viewer/` | New (v0.6.1) — `qm.view(design)` headless entry point. |
| `src/qiskit_metal/_gui/` | The Qt desktop GUI (`MetalGUI`). Hard-touch zone unless you have a Qt session to test in. |
| `src/qiskit_metal/analyses/` | Pure-Python analyses (Hamiltonian, capacitance, EPR). qutip 5+. |
| `tests/` | unittest-style suite. `pytest tests/` to run; gated in CI on every PR. |
| `tutorials/` | 40+ Jupyter notebooks. Numbered (1-Overview / 2-Components / 3-Renderers / 4-Analysis). |
| `docs/` | Sphinx. `tox -e docs` to build. |
| `scripts/check_env_consistency.py` | CI gate that asserts `environment.yml` and `pyproject.toml` agree. |

## Hard constraints — do not touch without explicit human approval

1. **`renderers/renderer_ansys/`** — COM-based HFSS/Q3D. Requires Ansys
   AEDT on Windows to validate. Even type-comparison changes have
   shipped silent bugs.
2. **`renderers/renderer_ansys_pyaedt/`** — same constraint for the
   pyaedt-based replacement.
3. **`_gui/` and everything inside it** — requires interactive Qt
   session to verify behavior.
4. **The pyEPR integration bridge** (`renderer_ansys/parse.py`,
   `solution_types.py` interaction with `pyEPR.solution_types`).
   Cross-repo coordination required.
5. **Public method signatures on `QComponent`, `QDesign`,
   `QRenderer`** — no breaking changes without deprecation path.

**If you find a real bug in any of the above, document it (e.g. in a
test's `KNOWN_*` skip list, see `tests/test_qlibrary_pin_sanity.py`)
rather than silently fixing.** A drive-by "fix" without HFSS / Qt
validation is how silent S-parameter errors ship.

## Read these next — context files

| File | Read when |
|------|-----------|
| `.claude/context/lessons-learned.md` | **Always.** Every hard-won fix from real debugging — pandas-2.2 indexing, qutip-5 API, lazy Qt, uv-auto-sync, the v0.6.0 release failure, etc. Avoids re-discovering each from scratch. |
| `.claude/context/architecture.md` | When you need to make structural changes — class hierarchy, option flow, renderer dispatch, lazy-Qt design. |
| `.claude/context/ecosystem.md` | When making roadmap / API / version decisions — who the users are, the pyEPR/pyaedt/AWS-Palace relationships, the v0.7.0 lite-by-default plan. |
| `docs/architecture/renderer_protocol.md` | When adding or modifying a renderer. The full inheritance map and override matrix. |
| `docs/headless-usage.rst` | When working on the Qt-free path or onboarding flow. |

## Recurring tasks — slash commands

| Command | What it does |
|---------|--------------|
| `.claude/commands/health-check.md` | `/health-check` — broad repo audit: CI status, deps, lint, test coverage, drift, recent activity. |
| `.claude/commands/release.md` | `/release` — step-by-step release procedure including the post-mortem of the v0.6.0 failure. |
| `.claude/commands/headless-check.md` | `/headless-check` — verify `import qiskit_metal` and `qm.view(design)` work without PySide6. Reproduces the `tests-lite` CI job locally. |
| `.claude/commands/refresh-tutorial.md` | `/refresh-tutorial` — apply the standard "no-Qt callout" to a tutorial or batch of tutorials. |

## Testing & CI quick reference

- Full suite: `QISKIT_METAL_HEADLESS=1 uv run pytest tests/` (~30s)
- Lint: `uvx ruff check src` (currently 13 known findings, all in
  HFSS/`_gui/` zones — see lessons-learned)
- Format: `uvx ruff format src`
- Docs build: `tox -e docs`
- Env-drift check: `uv run scripts/check_env_consistency.py`

CI matrix on every PR: 9 test combos (py3.10/3.11/3.12 ×
ubuntu/macos/windows) + `lint` + `env-consistency` + `coverage` +
`tests-lite` (including notebook-execute).

## Status snapshot (as of v0.6.1, May 2026)

- Latest release: **v0.6.1** on PyPI (after the v0.6.0 tag-only
  failure — see `.claude/commands/release.md`)
- Test count: **~475 passing**, 0 failing, 0 flaky
- New no-Qt path: `qm.view(design)` works with `pip install
  quantum-metal[lite]` (and the default install too — additive in
  v0.6.x; planned default flip in v0.7.0)
- HFSS 2024.1+ solution-type rename: handled via
  `solution_types.py` + pyEPR 0.9.5 normalisation
- qutip 5+ compatibility: shipped in v0.6.0/0.6.1
- 13 ruff findings deferred (all in HFSS/`_gui/` zones — need
  validation)
- 1 known HFSS bug deferred: `LaunchpadWirebondDriven.in` pin points
  inward (see `tests/test_qlibrary_pin_sanity.py` `KNOWN_INWARD_PINS`)
- AWS Palace integration on the roadmap — will unblock HFSS-free
  validation of the above
