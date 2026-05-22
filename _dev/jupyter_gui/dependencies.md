# Dependency Analysis

The core tension: every new dependency is a new failure mode for users on
cloud environments where you can't `pip install` freely, and a new thing to
pin, test, and maintain across Python 3.10–3.12.

---

## Three GUIs — they coexist, not replace each other

There are now **three** ways to view/interact with a Metal design. They are
independent — installing one does not affect the others.

| Entry point | Extra | What it is |
|-------------|-------|------------|
| `qm.view(design)` | (base — no extra needed) | Static matplotlib figure. Fast, headless, works in scripts and CI. Zero new deps. |
| `qm.MetalGUI` | `[gui]` (PySide6) | Full Qt desktop GUI. Windows/macOS native. Requires display; breaks Colab/Binder. |
| `qm.gui(design)` | `[notebook]` (new) | Jupyter widget GUI. ipywidgets + ipympl. Works everywhere Jupyter runs. |

Do NOT treat `qm.gui()` as a replacement for `qm.view()` or `MetalGUI` — it
is a third option for a different runtime context.

---

## Reality check: what's actually installed

`ipywidgets` and `ipympl` are **not** in `[project.optional-dependencies]`.
They are in `[dependency-groups] jupyter` (uv dev group — used for running
tutorials locally, not installed for end users). A user who does
`pip install quantum-metal` does not have them. They must be declared in a
new user-installable extra.

**IMPORTANT: `[gui]` is already taken.** The existing pyproject.toml has:
```toml
[project.optional-dependencies]
    gui = ["pyside6>=6.8", "qdarkstyle>=3.1"]   # ← MetalGUI / Qt desktop
```
Do NOT add ipywidgets to `[gui]` — that would mix two incompatible runtime
models and bloat every `pip install 'quantum-metal[gui]'` with Jupyter deps.

**The new extra must be named `[notebook]`:**

```toml
# pyproject.toml — add alongside existing [gui]
[project.optional-dependencies]
    gui      = ["pyside6>=6.8", "qdarkstyle>=3.1"]          # existing — do not change
    notebook = ["ipywidgets>=8.0", "ipympl>=0.9"]            # NEW — Jupyter widget GUI
    full     = [                                              # update to include notebook
        "pyside6>=6.8", "qdarkstyle>=3.1",
        "ipywidgets>=8.0", "ipympl>=0.9",
        "pyaedt>=0.21,<0.24", "pyEPR-quantum>=0.9.5",
        "gmsh>=4.15.0,<5",
    ]
```

**Install for the Jupyter GUI:**
```bash
pip install 'quantum-metal[notebook]'
# or for everything:
pip install 'quantum-metal[full]'
```

**There is no `[lite]` extra** — this is only a conceptual label in comments
inside pyproject.toml. The base install (`pip install quantum-metal`) is the
"lite" install. Do not reference `[lite]` in code or error messages.

---

## What's actually free (already in the install)

| Package | Already in... | What we get |
|---------|--------------|-------------|
| `matplotlib` | Core dep | Rendering via existing `QMplRenderer` |
| `pandas` | Core dep | QGeometry tables are already DataFrames |
| `pygments` | Jupyter itself (not our dep) | Syntax highlighting — use try/except, not a hard dep |

---

## Packages we must declare (new for the `[notebook]` extra)

| Package | Version | Why | Risk |
|---------|---------|-----|------|
| `ipywidgets` | `>=8.0` | All panels, layout, reactivity | Low — Jupyter standard, stable API |
| `ipympl` | `>=0.9` | Interactive matplotlib canvas | Low — already used in dev environment |

**Target ipywidgets 8.x only.** The 7.x API differs meaningfully:
- 7.x: `tab.set_title(i, 'name')` — 8.x: `Tab(titles=[...])` or `tab.titles = [...]`
- 8.x: `Accordion(titles=[...])` constructor — 7.x: only `set_title()`
The code will use 8.x throughout. If a user has 7.x, they get a clear error from the
version pin, not a cryptic AttributeError.

---

## Critical: backend activation

`ipympl` only produces an interactive widget if it is the **active matplotlib
backend** when the figure is created. The GUI cannot silently create a static
`Agg` figure and call it interactive.

The `gui()` function must handle this:

```python
def gui(design, ...):
    import matplotlib as _mpl
    backend = _mpl.get_backend().lower()
    
    # ipympl backends: 'module://ipympl.backend_nbagg' or 'widget'
    is_interactive = 'ipympl' in backend or 'widget' in backend
    
    if not is_interactive:
        # Try to switch — will fail silently in scripts, that's fine
        try:
            _mpl.use('module://ipympl.backend_nbagg')
            is_interactive = True
        except Exception:
            pass
    
    if not is_interactive:
        raise RuntimeError(
            "qm.gui() requires an interactive matplotlib backend.\n"
            "Add this before importing matplotlib:\n\n"
            "    %matplotlib widget\n\n"
            "or in a script:\n\n"
            "    import matplotlib\n"
            "    matplotlib.use('module://ipympl.backend_nbagg')\n\n"
            "Then: pip install 'quantum-metal[notebook]' if ipympl is not installed."
        )
```

---

## Options considered and rejected

### `ipytree`
Used for: the component library browser as a folder tree.

**Decision: use flat `Select` list (zero new deps).** The library browser
is not the primary interaction surface — most users add components by name,
not by browsing a file tree. Add `ipytree` as an optional future enhancement
if users request it. No flat `Select` → tree upgrade path needed in the API
(it's an internal implementation detail).

### `ipydatagrid`
A polished editable grid widget for the elements/variables tables.

**Decision: rejected.** Has a compiled C++ extension — fails on some cloud
environments. `pandas` `Styler` + `Output` widget is sufficient. Tables
in this GUI are read-heavy, not write-heavy.

### `anywidget`
Custom JavaScript canvas for the chip view — WebGL, SVG, or Canvas 2D.

**Decision: deferred to Tier 2 (v0.8.0).** The matplotlib canvas is good
enough for Tier 1. `anywidget` requires TypeScript contributors and a JS
build pipeline. Decision point: if users report canvas performance issues
on designs with >100 components, revisit.

### `Panel` (HoloViz)
Full dashboarding framework.

**Decision: rejected.** Pulls in Bokeh (~50 MB). Layout system diverges from
ipywidgets — contributors need to learn both. The cross-env portability
advantage Panel offers is already covered by ipywidgets.

### `Plotly Dash`
Spins up an HTTP server from inside the notebook.

**Decision: rejected.** Port-exposure breaks Colab, Binder, JupyterHub by
default. Not "inside" the notebook.

### `JupyterLab extension` (TypeScript)
**Decision: rejected.** Only works in JupyterLab — breaks Colab, classic
notebook, VS Code Jupyter.

---

## Constraint: cloud environments

| Environment | ipywidgets | ipympl | Port binding |
|-------------|-----------|--------|--------------|
| Google Colab | ✓ (built-in) | ✓ (pip install) | ✗ blocked |
| Binder | ✓ (built-in) | ✓ (requirements.txt) | ✗ blocked |
| JupyterHub | ✓ (built-in) | depends on admin | ✗ blocked |
| VS Code Jupyter | ✓ since 1.80 | ✓ | N/A |
| Local JupyterLab | ✓ | ✓ | N/A |

All of our chosen stack (ipywidgets + ipympl) works in every row above.
Anything that requires port binding (Dash, Panel server mode) is ruled out.

---

## Import cost — lazy loading

`qiskit_metal/__init__.py` must NOT do `from .jupyter_gui import gui` at the
top level. That would force an `ipywidgets` import every time anyone does
`import qiskit_metal` — including in scripts, CI, and headless analysis jobs
where ipywidgets is not installed.

**Required pattern:**

```python
# src/qiskit_metal/__init__.py

def gui(design, **kwargs):
    """Jupyter-native GUI. Requires quantum-metal[gui]."""
    try:
        from .jupyter_gui import gui as _gui
    except ImportError:
        raise ImportError(
            "qm.gui() requires ipywidgets and ipympl.\n"
            "Install with: pip install 'quantum-metal[notebook]'"
        ) from None
    return _gui(design, **kwargs)
```

This way `import qiskit_metal` stays fast and dep-free even if ipywidgets
isn't installed.
