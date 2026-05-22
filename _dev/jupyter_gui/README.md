# Jupyter GUI — Planning & Prototype Area

Targeting **v0.7.0**. This folder is the working area for designing and
prototyping `qm.gui()` — a Jupyter-native widget GUI using ipywidgets + ipympl.

## This is NOT a replacement

There are three distinct viewers. All three coexist:

| Viewer | Install | Context |
|--------|---------|---------|
| `qm.view(design)` | base (no extra) | Static matplotlib figure — scripts, CI, headless |
| `qm.MetalGUI` | `quantum-metal[gui]` | Qt desktop GUI — Windows/macOS with display |
| `qm.gui(design)` | `quantum-metal[notebook]` | Jupyter widget — Colab, Binder, JupyterHub, local |

## Goal

A single function call that works everywhere Jupyter runs — locally,
Colab, Binder, JupyterHub, VS Code — with no Qt dependency:

```python
# In a notebook cell:
%matplotlib widget
import qiskit_metal as qm
gui = qm.gui(design)   # returns a live ipywidgets widget
```

Install: `pip install 'quantum-metal[notebook]'`

## Files in this folder

| File | Purpose |
|------|---------|
| `README.md` | This file — orientation |
| `feature-map.md` | Panel-by-panel port from MetalGUI → ipywidgets |
| `plan.md` | Phased implementation plan with tasks |
| `dependencies.md` | Dependency options, risk analysis, install extras |
| `api-sketch.md` | Public API design + internal class structure |
| `concerns.md` | Deeper architectural concerns from pass 4 review + prototype proposal |
| `prototype.py` | Throwaway prototype implementing the new architecture |
| `prototype.ipynb` | Notebook exercising the prototype — for visual + perf validation |
| `prototype-findings.md` | What the prototype validated and what it broke |

## Status

- [x] MetalGUI audit complete (see `feature-map.md`)
- [x] Architecture decision made (see `dependencies.md`)
- [x] Two red team passes — all known bugs in planning docs corrected
- [ ] Phase 0 — setup: branch, stubs, pyproject.toml `[notebook]` extra
- [ ] Phase 1 scaffold — layout + canvas
- [ ] Phase 2 — click selection + highlight
- [ ] Phase 3 — options editor (edit + rebuild)
- [ ] Phase 4 — library browser + add component
- [ ] Phase 5 — remaining panels + polish

## Where the code will live

`src/qiskit_metal/jupyter_gui/` — new subpackage.
Re-exported at top level as `qm.gui` via a lazy wrapper function in
`src/qiskit_metal/__init__.py` (lazy so `import qiskit_metal` stays fast
even when ipywidgets is not installed).
