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

Stack: Python 3.10–3.14 · `shapely` for geometry · `geopandas` /
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
| `docs/tut/` | The tutorial notebooks (1-Overview / 2-From-components-to-chip / 3-Renderers / 4-Analysis, Appendix B, Appendix A reference designs). Hyphenated names; Sphinx renders them. See "Tutorial notebooks" below. |
| `docs/circuit-examples/` | Appendix C circuit examples and the Appendix A full-design-flow notebooks. |
| `tutorials/` | Only a README mapping the old notebook paths to their `docs/` homes (the notebooks moved in September 2026). |
| `docs/` | Sphinx. `tox -e docs` to build. |
| `scripts/check_env_consistency.py` | CI gate that asserts `environment.yml` and `pyproject.toml` agree. |

## Tutorial notebooks — read before editing them

Every notebook has exactly one copy, under `docs/`:

| Path                        | What lives there                                                      |
|-----------------------------|-----------------------------------------------------------------------|
| `docs/tut/`                 | Numbered tutorials (1.x, 2.xx, 3.x, 4.xx), Appendix B, and the Appendix A reference designs |
| `docs/circuit-examples/`    | Appendix C, plus the remaining Appendix A full-design-flow examples   |
| `docs/tut/resources/`       | Input files notebooks load (junction GDS, layer stacks, helper modules) |

Until September 2026 each notebook also lived in `tutorials/` (names with
spaces) and a sync script plus CI check kept the copies identical; the
second copy was removed and `tutorials/README.md` maps old paths to new.
Don't reintroduce a second tree.

Stored cell **outputs** are what the docs site shows: the docs build does not
execute notebooks (`nbsphinx_execute = "never"` unless
`QISKIT_DOCS_BUILD_TUTORIALS` is set). Keep outputs when you edit a notebook,
and re-execute it when the code changes what it prints or draws (in a scratch
copy, so files the notebook writes stay out of the repo).

Notebooks that are kept but not on the site are listed in `exclude_patterns`
in `docs/conf.py`. Colab/Binder badges and raw-download URLs point at the
notebook's own `docs/` path.

## Hard constraints — do not touch without explicit human approval

1. **`renderers/renderer_ansys/`** — COM-based HFSS/Q3D. Requires Ansys
   AEDT on Windows to validate. Even type-comparison changes have
   shipped silent bugs.
2. **`renderers/renderer_ansys_pyaedt/`** — same constraint for the
   pyaedt-based replacement.
3. **`_gui/` and everything inside it** — requires interactive Qt
   session to verify behavior. **Startup, teardown, stylesheet handling
   and persisted window state additionally require reading
   `docs/architecture/gui_crash_defenses.md` first.** Those paths carry
   defenses from a five-release segfault hunt (issue #1048) that look
   removable and are not; CI passing is not sufficient evidence there,
   because the reported crashes never reproduced on CI runners.
4. **The pyEPR integration bridge** (`renderer_ansys/parse.py`,
   `solution_types.py` interaction with `pyEPR.solution_types`).
   Cross-repo coordination required.
5. **Public method signatures on `QComponent`, `QDesign`,
   `QRenderer`** — no breaking changes without deprecation path.

**If you find a real bug in any of the above, document it (e.g. in a
test's `KNOWN_*` skip list, see `tests/test_qlibrary_pin_sanity.py`)
rather than silently fixing.** A drive-by "fix" without HFSS / Qt
validation is how silent S-parameter errors ship.

## Public commits, PRs, and files — keep them terse and factual

Anything that lands in git is public, searchable, and permanent. Keep
commit messages, PR descriptions, and any files under `_dev/` (yes,
even there — `_dev/` is committed scratch, not local-only) to the
**factual, attributable minimum**:

- Describe **what changed and why technically**. Skip strategic
  reasoning, competitive framing, and adoption / DevRel commentary —
  those belong in chat with the maintainer, not in the repo.
- **Don't characterise people** beyond standard public attribution
  (name + repo + license). Backgrounds, productivity adjectives,
  affiliations beyond what they list on their own profile, "solo but
  prolific" — out.
- **Don't draft outreach in committed files.** Outreach messages,
  "if they say X we do Y" matrices, talking points, negotiation
  strategy — chat only. The maintainer copies, edits, and sends.
- **Don't editorialise about other projects** ("don't absorb their
  repo", "their packaging is broken", "they're more active than us") —
  describe technical facts (license, integration shape, API surface)
  and stop.
- When in doubt, default to a one-line attribution + link. The reader
  can click through.

If the maintainer asks for strategic analysis, give it in chat.
Don't reach for `_dev/` as a halfway house — it's still public.

| File | Read when |
|------|-----------|
| `.claude/context/lessons-learned.md` | **Always.** Every hard-won fix from real debugging — pandas-2.2 indexing, qutip-5 API, lazy Qt, uv-auto-sync, the v0.6.0 release failure, etc. Avoids re-discovering each from scratch. |
| `.claude/context/decision-log.md` | Before undoing something that looks odd, or picking up deferred work. Records *why* we chose an approach and what we deliberately did **not** do (e.g. the deferred ruff-0.16 rule adoption). Append an entry when you make a non-obvious call — **read the callout at the top of that file first; it is a public document.** |
| `.claude/context/architecture.md` | When you need to make structural changes — class hierarchy, option flow, renderer dispatch, lazy-Qt design. |
| `.claude/context/ecosystem.md` | When making roadmap / API / version decisions — who the users are, the pyEPR/pyaedt/AWS-Palace relationships, the v0.7.0 lite-by-default plan. |
| `docs/architecture/renderer_protocol.md` | When adding or modifying a renderer. The full inheritance map and override matrix. |
| `docs/architecture/gui_crash_defenses.md` | **Before touching GUI startup, teardown, stylesheet handling, or persisted window state.** The four distinct failure modes behind issue #1048, every defense and what it guards, the ordering constraints (notably: the startup journal must stay open across `show()`, and all deferred callbacks go through `single_shot()` — an "Internal C++ object already deleted" anywhere in output is a use-after-free report, never noise), and the changes that look safe but reintroduce segfaults. |
| `docs/architecture/open_fem_scikit_fem.md` | Before reusing or extending the gmsh + scikit-fem Maxwell solver of tutorials 4.41–4.45 (`qiskit_metal.analyses.fem`; the analytic models in `qiskit_metal.analyses.em.package_modes`; the tutorials' own device and design in `docs/tut/resources/package_modes/`). Conventions, validation numbers, the physics that bites (the edge-element model's qubit capacitance is P1 electrostatics on the same mesh), limitations, and the path to a reusable backend. |
| `docs/headless-usage.rst` | When working on the Qt-free path or onboarding flow. |
| `.claude/skills/chip-design/SKILL.md` | When designing a new chip or a variant from a specification. Spec and frequency plan, floorplan, staged build with DRC per stage, cell simulation, and the build rules that fail silently (unterminated ends, unwired airbridges, starved fillets, rotation vs pin angle). |
| `.claude/skills/chip-layout-from-images/SKILL.md` | When reproducing a published device from its images, as a benchmark or for teaching. Measurement from pixels and conformance to the source; credit and scope rules. |
| `.claude/skills/chip-simulation/SKILL.md` | When simulating a cell, an array or a package and extracting frequencies, capacitances or couplings (Ansys, ElmerFEM, or the gmsh + scikit-fem solver). Solver choice, validation against analytic cases, mesh seeding and convergence, symmetry, junctions as lumped elements, and what each coupling-extraction method can and cannot give. |
| `.claude/skills/tutorial-notebook/SKILL.md` | When writing or re-running tutorial notebooks. Structure, shared resource modules, builder scripts, reliable execution (kernel, working folder, dead-kernel check), reviewing every figure, and keeping stored outputs free of local paths and log noise. |

## Adding a new QComponent

When you add a class in `qlibrary/`, run the thumbnail generator so the
Library pane in `MetalGUI` shows a real preview instead of the
placeholder logo:

```bash
QISKIT_METAL_HEADLESS=1 uv run python _dev/generate_qlibrary_thumbnails.py \
    --write --inject-docstrings
```

Outputs PNGs to `src/qiskit_metal/_gui/_imgs/components/<ClassName>.png`
and inserts a `.. image:: <ClassName>.png` directive after the class
docstring's summary line if missing. Both are checked in. Only missing PNGs
are rendered (`--force` redraws all); look at the new PNG and the docstring
before committing.

If your component needs pins / anchors / non-default options to render
meaningfully (e.g. a Route), add a recipe to `SPECIAL_RECIPES` near the
top of that script — recipes are callables that return
`(design, component)`. The script already has examples for the
`Route*` classes.

The same images are referenced by the Sphinx API docs, so the docstring
augmentation is "do once, render everywhere."

## Auto-generated docs assets

To avoid duplicating ~100 PNGs across `src/qiskit_metal/_gui/_imgs/components/`
(runtime source of truth for the Qt `MetalGUI`), `docs/apidocs/`
(referenced by autodoc class docstrings), and `docs/images/qlibrary/`
(referenced by the visual gallery), the latter two — plus
`docs/qcomponents-gallery.rst` — are **generated at every docs build**.

The Sphinx `builder-inited` hook in `docs/conf.py` runs
`_dev/generate_qcomponent_gallery.py --write` and a small scaffold-icon
copy step before any reading happens. Source of truth is the
`_gui/_imgs/` directory + each class' `.. image::` docstring directive.

Gitignored (regenerated):
- `docs/qcomponents-gallery.rst`
- `docs/images/qlibrary/`
- `docs/apidocs/*.png`

Still tracked:
- `src/qiskit_metal/_gui/_imgs/components/*.png` (runtime source)
- `docs/apidocs/*.rst` (autosummary-generated, but historically committed)

If a fresh checkout's docs build can't find a thumbnail, the source
PNG is missing under `_gui/_imgs/components/` — re-run
`uv run python _dev/generate_qlibrary_thumbnails.py --write
--inject-docstrings` to regenerate it from each component's
`make()` output. The build hook only *copies* existing source PNGs;
it doesn't generate missing ones (that requires importing each
component, which is too slow for a hot docs-build path).

## Recurring tasks — slash commands

| Command | What it does |
|---------|--------------|
| `.claude/commands/health-check.md` | `/health-check` — broad repo audit: CI status, deps, lint, test coverage, drift, recent activity. |
| `.claude/commands/release.md` | `/release` — step-by-step release procedure including the post-mortem of the v0.6.0 failure. |
| `.claude/commands/headless-check.md` | `/headless-check` — verify `import qiskit_metal` and `qm.view(design)` work without PySide6. Reproduces the `tests-lite` CI job locally. |
| `.claude/commands/refresh-tutorial.md` | `/refresh-tutorial` — apply the standard "no-Qt callout" to a tutorial or batch of tutorials. |

## Testing & CI quick reference

- Full suite: `QISKIT_METAL_HEADLESS=1 uv run pytest tests/` (~30s)
- Lint: `uvx ruff check src` (clean, 0 findings — see Status snapshot)
- Format: `uvx ruff format src`
- Docs build: `tox -e docs`
- Env-drift check: `uv run scripts/check_env_consistency.py`

CI matrix on every PR: 9 test combos (py3.10–3.14 on ubuntu;
py3.10 and 3.14 on macos/windows) + `lint` + `env-consistency` + `coverage` +
`tests-lite` (including notebook-execute) + `tests-deps-pandas3` /
`tests-deps-lowest` (dependency bounds outside `uv.lock`).

## Status snapshot (as of v0.9.0, September 2026)

- Latest release: **v0.9.0** (September 2026) — Python 3.13/3.14, numpy
  2 support with raised dependency minimums, and analysis/renderer/tutorial
  fixes. v0.8.1 was GUI stability and interactive editing; v0.8.0 added
  design-rule checking (`qiskit_metal.validation`, #1169) and the
  `QMplRenderer` die outline. (**Note:** a `v0.7.7`
  tag/GitHub Release exist on `a7efeeb1` but were never published to
  PyPI — see `changelog.md`. PyPI went 0.7.6 → 0.8.0 directly.)
- Test count: **~865 collected** with all extras installed (GUI
  display tests skip without a display). macOS GUI subprocess tests
  (`test_gui_init`, `test_gui_nudge`) occasionally hit a native crash
  in the child (#1048); their failure output now shows the crash stack
  via `tests/_crash_output.py`
- Lite-by-default (shipped in v0.7.0): `qm.view(design)` and headless
  use work with the default `pip install quantum-metal`; the desktop
  GUI moved to the `[gui]` extra
- HFSS 2024.1+ solution-type rename: handled via
  `solution_types.py` + pyEPR 0.9.5 normalisation
- qutip 5+ compatibility: shipped in v0.6.0/0.6.1
- **`ruff check src` is clean (0 findings)** — the 13 previously
  deferred findings (E721/E711/F811/F822 in HFSS/`_gui/`) have since
  been resolved in `src`
- 1 known HFSS bug deferred: `LaunchpadWirebondDriven.in` pin points
  inward (see `tests/test_qlibrary_pin_sanity.py` `KNOWN_INWARD_PINS`)
- AWS Palace integration on the roadmap — will unblock HFSS-free
  validation of the above
