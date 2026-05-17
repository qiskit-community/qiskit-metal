# Renderer protocol audit

This is a read-only inventory of qiskit-metal's renderer class hierarchy
as of v0.6.1. It exists so a contributor or HFSS-savvy reviewer can
spot gaps without re-discovering the hierarchy each time.

## TL;DR

There are **two** abstract base classes in `renderers/renderer_base/`:

| Base | Purpose | Abstract methods |
|------|---------|------------------|
| `QRenderer` | Top-level interface, suitable for **export-only** renderers (GDS, Gmsh). | 3 |
| `QRendererAnalysis(QRenderer)` | Adds the per-element / per-chip render hooks that analysis renderers need. | 8 |

There are **9 concrete renderer classes** (10 if you count `QMplRenderer` — see caveat).

Every concrete renderer overrides its base's abstract methods (no
silent NotImplementedError surface). The one stub-only method I found
(`render_chip` at `ansys_renderer.py:1053`) is dead — the real
implementation is at line 1529. That F811 is in the "needs HFSS
review" bucket from the tier-0 ruff triage.

## Inheritance map

```
QRenderer (renderer_base.py)
├── _initiate_renderer()     [abstract]
├── _close_renderer()        [abstract]
└── render_design()          [abstract]

QRendererAnalysis(QRenderer) (rndr_analysis.py)
├── initialized              [abstract property]
├── render_chips()           [abstract]
├── render_chip(name)        [abstract]
├── render_components(...)   [abstract]
├── render_component(...)    [abstract]
├── render_element(...)      [abstract]
├── render_element_path(...)  [abstract]
├── render_element_poly(...) [abstract]
└── save_screenshot(...)     [abstract]
```

### Concrete renderers

```
QRenderer
├── QGDSRenderer             (renderer_gds/gds_renderer.py)        export-only
└── QGmshRenderer            (renderer_gmsh/gmsh_renderer.py)      export-only (FEM mesh)

QRendererAnalysis (which is itself a QRenderer)
├── QAnsysRenderer           (renderer_ansys/ansys_renderer.py)    legacy COM-based Ansys
│   ├── QHFSSRenderer        (renderer_ansys/hfss_renderer.py)
│   └── QQ3DRenderer         (renderer_ansys/q3d_renderer.py)
├── QPyaedt                  (renderer_ansys_pyaedt/pyaedt_base.py)  new pyaedt-based
│   ├── QHFSSPyaedt          (renderer_ansys_pyaedt/hfss_renderer_aedt.py)
│   │                         + QHFSSPyaedtDrivenmodal, QHFSSPyaedtEigenmode
│   └── QQ3DPyaedt           (renderer_ansys_pyaedt/q3d_renderer_aedt.py)
└── QElmerRenderer           (renderer_elmer/elmer_renderer.py)    open-source FEM

QMplRenderer  ⚠ NOT a QRenderer subclass — see caveat below.
```

## Two-track Ansys story (architectural observation)

Both `renderer_ansys/` (`QAnsysRenderer`) and `renderer_ansys_pyaedt/`
(`QPyaedt`) exist in parallel. They render the same designs to the
same Ansys backends but use different bridges:

* `renderer_ansys/` — original implementation, COM-based, Windows-only
  for the live solve path. Goes via `pyEPR.ansys` for the lower-level
  COM calls. Touched in the v0.6.0 work to handle the HFSS 2024.1+
  solution-type rename.
* `renderer_ansys_pyaedt/` — newer, uses the official `pyaedt` Python
  package (Ansys-supplied). Should eventually replace the COM-based
  path; the existence of both is the migration in progress.

**No deprecation policy is currently documented for the `renderer_ansys/`
track.** Worth deciding before adding new Ansys functionality.

## The `QMplRenderer` caveat

`renderers/renderer_mpl/mpl_renderer.py` defines `class QMplRenderer:`
— **with no parent class**. It is *not* a `QRenderer`. Despite being
in the `renderers/` directory, it's a Qt-canvas widget renderer, not
a design-export renderer.

Constructor signature:

```python
def __init__(self, canvas: "PlotCanvas", design: QDesign,
             logger: logging.Logger):
```

`PlotCanvas` is the Qt-based `mpl_canvas.PlotCanvas` widget. The whole
class is coupled to Qt via that constructor, so it can't be used
standalone (e.g. in Jupyter or on a headless cloud runner).

**Decoupling `QMplRenderer` from `PlotCanvas` is Tier 2 in the
maintenance plan** — it's the single change that unlocks a no-Qt
rendering path for Binder/Colab/JupyterLab tutorials.

A natural follow-on would be to either:

1. Make `QMplRenderer` accept an `ax: Optional[matplotlib.axes.Axes]`
   instead of a `PlotCanvas`, and synthesise a canvas internally only
   when needed (least disruptive — keeps existing call sites working).
2. Promote `QMplRenderer` to a `QRenderer` subclass with proper
   `_initiate_renderer` / `render_design` overrides, and make
   `PlotCanvas` consume *it* rather than the other way round (deeper,
   cleaner long-term).

(1) is the unblock-now path; (2) is the right architectural endpoint.

## Per-renderer override matrix

A `✓` means the renderer overrides the abstract method. A `inherits`
means it uses a non-abstract default. A `—` means N/A for this base.

| Method                | GDS | Gmsh | Ansys | HFSS | Q3D | Pyaedt | HFSSPyaedt | Q3DPyaedt | Elmer |
|-----------------------|:---:|:----:|:-----:|:----:|:---:|:------:|:----------:|:---------:|:-----:|
| `_initiate_renderer`  | ✓   | ✓    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `_close_renderer`     | ✓   | ✓    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `render_design`       | ✓   | ✓    | ✓     | ✓    | ✓   | ✓      | ✓          | ✓         | ✓     |
| `render_chips`        | —   | —    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `render_chip`         | —   | —    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `render_components`   | —   | —    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `render_component`    | —   | —    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `render_element`      | —   | —    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `render_element_path` | —   | —    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `render_element_poly` | —   | —    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |
| `save_screenshot`     | —   | —    | ✓     | inh. | inh.| ✓      | inh.       | inh.      | ✓     |

Sources: greps of `class …(QRenderer|QAnsysRenderer|QPyaedt|…)` and
`def render_*` / `def _initiate_renderer` / `def _close_renderer`
across `src/qiskit_metal/renderers/`. The `inh.` cells were verified
by walking each MRO.

## Known issues

1. **Dead `render_chip` stub** at
   `renderer_ansys/ansys_renderer.py:1053`. Just `def render_chip(self): pass`;
   the real implementation is 476 lines later at 1529. Ruff flags this
   as `F811 Redefinition of unused`. Listed in the tier-0 ruff
   skipped-because-HFSS bucket.
2. **No documented deprecation path** for the COM-based
   `renderer_ansys/` track despite the pyaedt-based replacement
   existing in `renderer_ansys_pyaedt/`. Adding new Ansys
   functionality has to land in both today, with no clear rule for
   when to stop.
3. **`QMplRenderer` is structurally outside the renderer protocol**
   (no `QRenderer` base). This is the Tier 2 target.
4. **No `QRenderer` subclass for SVG / PNG export.** A user who just
   wants a static image of a design currently has no good path
   without going through Qt. (Resolved as a side-effect of the Tier 2
   `QMplRenderer` decoupling: once it produces standalone `Figure`s,
   `fig.savefig(…)` is right there.)

## How to extend this document

If you add a new concrete renderer:

1. Add it to the inheritance map.
2. Add a column to the override matrix.
3. If you intentionally don't override an `inh.` method, write a
   sentence in "Known issues" explaining why your renderer can ignore
   it.

If you change `QRenderer` or `QRendererAnalysis` abstract surface:

1. Update the TL;DR counts.
2. Add the new method to the matrix and verify every existing
   renderer implements it (or is intentionally exempt).
