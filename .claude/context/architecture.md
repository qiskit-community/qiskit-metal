# Architecture — how Quantum Metal's pieces fit together

Read this when you need to make structural changes. For tactical
"don't trip on this" knowledge, see `lessons-learned.md`.

## The three load-bearing abstractions

### `QComponent` — `qlibrary/core/base.py`

A `QComponent` is a piece of geometry parameterised by an options
dict. Subclasses live in `qlibrary/` (transmons, terminations,
routes, etc.). Every component has:

- **`default_options`**: class-level `addict.Dict` of default
  parameter values
- **`make()`**: builds the geometry from `self.options` / `self.p`,
  calls `self.add_qgeometry(...)` and `self.add_pin(...)`
- **`rebuild()`**: clears prior geometry and calls `make()` —
  idempotent by design (see `tests/test_qlibrary_idempotency.py`)

Lifecycle: `__init__` → registers component on `design` → calls
`rebuild()` (which calls `make()`) → component sits in
`design.components` until deleted or re-built.

The `self.p` proxy is `ParsedDynamicAttributes_Component(self)` — a
view of `self.options` that parses string units (`"30um"` → numeric)
on attribute access. `make()` should generally read via `self.p`,
not `self.options` directly. Both are static-analysable —
`tests/test_default_options_completeness.py` AST-walks each `make()`
to assert every accessed key exists in the merged
`default_options`.

### `QDesign` — `designs/design_base.py`

The container for components, qgeometry, variables, and chip
metadata. Subclasses (`DesignPlanar`, `DesignFlipChip`, etc.) define
the chip stack.

Lifecycle: `__init__` → creates qgeometry tables → calls
`_start_renderers()` which loads every registered renderer
(gracefully skipping ones whose deps aren't installed, post-v0.6.1).

Components attach automatically when constructed with a design
argument: `TransmonPocket(design, "Q1")` registers itself on
`design.components["Q1"]`.

### `QRenderer` (and `QRendererAnalysis`) — `renderers/renderer_base/`

The output side. `QRenderer` has 3 abstract methods
(`_initiate_renderer`, `_close_renderer`, `render_design`);
`QRendererAnalysis(QRenderer)` adds 8 more for analysis-renderer
needs (per-component, per-element, per-chip dispatch).

Concrete renderers split into two camps:

- **Lightweight / export-only**: `QGDSRenderer`, `QGmshRenderer` —
  direct `QRenderer` subclasses
- **Analysis**: `QAnsysRenderer` (legacy COM), `QPyaedt` (new
  pyaedt-based), `QElmerRenderer` — `QRendererAnalysis` subclasses

`QMplRenderer` is a special case — it lives in `renderer_mpl/` but
**does not inherit from `QRenderer`**. It's structurally an
in-memory viewer that operates on the same `design.qgeometry.tables`
the proper renderers consume. As of v0.6.1 it's usable standalone
(no `PlotCanvas` required).

See `docs/architecture/renderer_protocol.md` for the full
inheritance map and override matrix.

## The two parallel Ansys tracks

Both `renderer_ansys/` (`QAnsysRenderer`) and
`renderer_ansys_pyaedt/` (`QPyaedt`) exist in the repo. They render
the same designs to the same backends via different bridges:

- `renderer_ansys/` — original, COM-based, goes through
  `pyEPR.ansys`. Windows-only at solve time. Handles the HFSS
  2024.1+ solution-type rename via `solution_types.py`.
- `renderer_ansys_pyaedt/` — newer, uses Ansys's official
  `pyaedt` package. Migration target but not yet feature-parity.

**No deprecation policy is currently documented for the older
track.** Any new Ansys feature lands in both. AWS Palace
integration on the roadmap may render this question moot (open
FEM path replaces Ansys for most users).

## Option flow

```
class TransmonPocket(BaseQubit):
    default_options = Dict(pad_width='455um', pad_height='90um', ...)
    #                       ↑
    #                       └─ class-level static
    
    def make(self):
        p = self.p                 # parsed proxy
        pad_width = p.pad_width    # "455um" → 0.000455 (meters)
        ...
```

At instantiation:

```
options = QComponent.get_template_options(design, ...)
        = merge(
            ancestor default_options chain,    # walked via MRO
            user options dict,                  # passed to __init__
            renderer-injected option columns,   # via setup_renderers
          )
```

The merged result becomes `self.options` (an `addict.Dict`). `self.p`
is a lazy parsing view over that.

**Static guarantee** (PR #1062): `tests/test_default_options_completeness.py`
AST-walks each component, collects every static `self.options.X` /
`self.p.X` access, asserts every key is present in the merged
defaults. Catches the silent `KeyError` class of bug at PR time
instead of at user runtime.

## QGeometry tables

`design.qgeometry.tables` is a dict of `{table_name: GeoDataFrame}`.
The three canonical tables:

- `poly` — filled shapes (qubit pads, pockets)
- `path` — line segments (CPWs, traces)
- `junction` — Josephson junction placeholders (rendered as zero-width)

Each row has columns: `component` (id), `name` (string per
component-name pair), `geometry` (shapely object), `chip`, `layer`,
`subtract`, `helper`, plus renderer-injected extras
(`fillet_radius`, `material`, etc.).

`QComponent.make()` populates these via `add_qgeometry('poly',
dict(name=shape, ...), layer=N, subtract=False)`.

## Lazy-Qt architecture (post v0.6.1)

Pre-v0.6.1, `import qiskit_metal` unconditionally imported PySide6.
Post-v0.6.1:

```
import qiskit_metal as qm        # no PySide6 import
fig = qm.view(design)            # no PySide6 import
qm.MetalGUI(design)              # NOW PySide6 imports (via __getattr__)
qm.plt.draw_design(...)          # NOW PySide6 imports (via __getattr__)
```

Mechanism:

1. `qiskit_metal/__init__.py` no longer calls `__setup_Qt_backend`
   at module load. Renamed to public `setup_qt_backend()` and called
   from `MetalGUI.__init__`.
2. `MetalGUI` and `plt` (alias for `renderer_mpl.mpl_toolbox`) are
   exposed via PEP-562 `__getattr__` on the top-level module — only
   imported on first attribute access.
3. `mpl_interaction.py` PySide6 imports are wrapped in `try/except
   ImportError`, with `_require_qt()` gates on the Qt-using
   functions (`figure_pz`).
4. `_start_renderers` in `design_base.py` catches `ImportError`
   from optional renderer modules (gmsh, pyaedt), skipping them
   gracefully on lite installs.

Net result: `pip install quantum-metal[lite]` (no PySide6, pyaedt,
gmsh) supports the full headless API. The `tests-lite` CI job
enforces this.

## v0.7.0 planned lite-by-default flip

Currently the `[gui]`, `[ansys]`, `[fem]`, `[full]` extras are
*additive* — the base install still pulls in everything. v0.7.0
plans to flip this:

- `pip install quantum-metal` → no Qt, no Ansys, no gmsh (lite by
  default)
- `pip install quantum-metal[full]` → current all-in install
- `pip install quantum-metal[gui]` → adds PySide6 + qdarkstyle
- `pip install quantum-metal[ansys]` → adds pyaedt + pyEPR
- `pip install quantum-metal[fem]` → adds gmsh

The infrastructure (lazy imports, graceful renderer skip, CI gate,
viewer module) is shipped in v0.6.1; the flip itself is a one-line
`pyproject.toml` change planned for v0.7.0.

## Test architecture

Five canonical test families in `tests/`:

| File | Scope |
|------|-------|
| `test_qlibrary_1_instantiate.py` | Every qlibrary class instantiates cleanly with default options |
| `test_qlibrary_idempotency.py` | `make()` is deterministic — rebuild twice, geometry matches |
| `test_qlibrary_pin_sanity.py` | Every pin has valid metadata: positive width, unit-norm normal, normal points outward |
| `test_default_options_completeness.py` | Every `self.options.X` access in `make()` exists in merged defaults |
| `test_viewer.py` | `qm.view(design)` returns a valid Figure on the lite venv |

Plus targeted unit tests for analyses, solution types, pyEPR
integration, etc. ~475 tests total as of v0.6.1.

## CI architecture

`.github/workflows/main.yml` defines:

| Job | Run on | Time |
|-----|--------|------|
| `tests-pythonX.Y-OS` (9 jobs) | py3.10/3.11/3.12 × ubuntu/macos/windows | ~2-3 min each |
| `lint` | ubuntu-py3.12, ruff | <1 min |
| `env-consistency` | ubuntu, runs `scripts/check_env_consistency.py` | <30s |
| `coverage` | ubuntu-py3.12, pytest --cov | ~3 min |
| `tests-lite` | ubuntu-py3.12, lite venv (no Qt/Ansys/gmsh) | ~30s |

`tests-lite` runs the headless test suite + executes the canonical
no-Qt tutorial (`1.4 Headless quick view`) via nbconvert. Failing
this job means a Qt import sneaked into a non-GUI module.

## Where new code goes

| You're adding... | It goes in... |
|------------------|---------------|
| A new `QComponent` | `src/qiskit_metal/qlibrary/<category>/<name>.py` + tests in `tests/test_qlibrary_*` |
| A new analysis | `src/qiskit_metal/analyses/<topic>/<name>.py` |
| A new renderer | `src/qiskit_metal/renderers/renderer_<name>/<name>_renderer.py`, inherit from `QRenderer` or `QRendererAnalysis` |
| A user-facing helper | `src/qiskit_metal/<topic>/__init__.py` (e.g. `viewer/`) |
| A CI gate | `.github/workflows/main.yml` step + `scripts/<gate>.py` if non-trivial |
| Docs page | `docs/<topic>.rst`, add to `docs/index.rst` toctree |
| Tutorial notebook | `tutorials/<folder>/X.Y Name.ipynb` with the standard "no-Qt callout" at top |
