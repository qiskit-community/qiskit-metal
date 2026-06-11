# API & Internal Structure Sketch

## Public API

Three viewers — all coexist, none replaces the others:

```python
import qiskit_metal as qm

# 1. Static matplotlib figure — base install, works in scripts and CI
qm.view(design)                    # no extra needed

# 2. Qt desktop GUI — requires quantum-metal[gui] (PySide6, Windows/macOS)
gui = qm.MetalGUI                  # existing — not changed

# 3. Jupyter widget GUI — requires quantum-metal[notebook] (ipywidgets+ipympl)
#    %matplotlib widget  ← must be in the cell above
gui = qm.gui(design)               # this file describes only this one

# With options
gui = qm.gui(
    design,
    height=700,          # canvas height in pixels
    show_log=True,       # show log panel
    show_library=True,   # show library browser panel
    theme='dark',        # 'dark' | 'light' (uses mpl.style.context, not global plt.style.use)
)

# The returned object IS the widget — display it
gui                      # Jupyter auto-displays
display(gui)             # explicit display
gui.close()              # detaches log handler — call when done or re-running cell
```

`qm.gui` is a lazy wrapper in `qiskit_metal/__init__.py` alongside `qm.view`.
Install: `pip install 'quantum-metal[notebook]'`

---

## Internal class structure

```
src/qiskit_metal/jupyter_gui/
├── __init__.py           # exports gui()
├── gui.py                # gui() entry point, assembles layout
├── canvas.py             # CanvasPanel — ipympl figure + render loop
├── panels/
│   ├── component_list.py # ComponentListPanel
│   ├── options.py        # OptionsPanel (recursive form)
│   ├── library.py        # LibraryPanel (component browser + add form)
│   ├── variables.py      # VariablesPanel
│   ├── elements.py       # ElementsPanel (QGeometry tables)
│   ├── netlist.py        # NetlistPanel
│   └── log.py            # LogPanel + OutputWidgetHandler
├── toolbar.py            # ToolbarRow (top buttons)
├── state.py              # GuiState — single shared state object
└── utils.py              # options_to_widgets(), set_nested(), etc.
```

---

## GuiState — the glue

All panels communicate through a single shared state object, not through
direct references to each other. This keeps panels decoupled.

```python
# state.py
import ipywidgets as W

class GuiState:
    """Shared reactive state. Panels observe this, not each other."""

    def __init__(self, design):
        self.design = design

        # Currently selected component name (None if nothing selected)
        self.selected = W.Text(value='')

        # Rebuild-needed flag (set when options edited, cleared after rebuild)
        self.dirty = W.ToggleButton(value=False)

    def select(self, name: str):
        self.selected.value = name or ''

    def mark_dirty(self):
        self.dirty.value = True

    def mark_clean(self):
        self.dirty.value = False
```

Each panel:
```python
class OptionsPanel:
    def __init__(self, state: GuiState):
        self.state = state
        state.selected.observe(self._on_selection_change, names='value')

    def _on_selection_change(self, change):
        name = change['new']
        if name and name in self.state.design.components:
            self._load_component(self.state.design.components[name])
        else:
            self._show_placeholder()

    def _load_component(self, comp):
        # Help tab: safe — docstrings are always strings
        doc = inspect.getdoc(comp.__class__) or '(no docstring)'

        # Source tab: wrap in try/except — inspect.getsource() raises OSError
        # for built-in or dynamically-defined classes, and in some frozen envs.
        try:
            src = inspect.getsource(comp.__class__)
        except (OSError, TypeError):
            src = '(source not available)'

        # ... build widgets from doc and src ...
```

---

## Canvas panel internal flow

```python
class CanvasPanel:
    def __init__(self, state: GuiState, height=600, mpl_style='dark_background'):
        self.state = state
        self.renderer = QMplRenderer(design=state.design)
        self._style = mpl_style  # stored so render() can use same style on every redraw

        # Create figure inside style context — bakes facecolor/edgecolor into the figure.
        # We also pass _style to render() so ax.cla() + re-render stays dark.
        import matplotlib as mpl
        with mpl.style.context(self._style):
            self.fig, self.ax = plt.subplots(figsize=(8, height/100))
        self.fig.canvas.toolbar_visible = True
        self.fig.canvas.header_visible = False

        # Click → select component
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

        self.widget = self.fig.canvas  # the ipympl widget

    def render(self):
        # ax.cla() resets axes — must re-apply style on each render so the
        # background stays dark after the initial creation's rc_context ends.
        import matplotlib as mpl
        with mpl.style.context(self._style):
            self.ax.cla()
            self.renderer.render(self.ax)
            self._draw_highlight()
        self.fig.canvas.draw_idle()  # draw_idle outside context — it just schedules a repaint

    def _on_click(self, event):
        if event.inaxes != self.ax:
            return
        x, y = event.xdata, event.ydata
        name = self._find_nearest_component(x, y)
        if name:
            self.state.select(name)

    # Debounce note: _on_click triggers state.select() which fires all observers
    # including canvas.render() (for the highlight redraw). render() calls
    # QMplRenderer which is ~100ms on a 50-component design. This is acceptable
    # for a click event. For motion_notify_event (hover), do NOT trigger a full
    # render — only update a status label widget.

    def _find_nearest_component(self, x, y):
        """Return name of component whose bounding box centroid is
        nearest to (x, y). Falls back to bounding box overlap check."""
        # qgeometry_bounds() returns a numpy array [minx, miny, maxx, maxy]
        best, best_dist = None, float('inf')
        for name, comp in self.state.design.components.items():
            try:
                bounds = comp.qgeometry_bounds()  # numpy array [minx, miny, maxx, maxy]
                cx = (bounds[0] + bounds[2]) / 2
                cy = (bounds[1] + bounds[3]) / 2
                d = (x - cx)**2 + (y - cy)**2
                if d < best_dist:
                    best_dist = d
                    best = name
            except Exception:
                pass
        return best

    def zoom_to(self, name: str):
        comp = self.state.design.components.get(name)
        if comp is None:
            return
        b = comp.qgeometry_bounds()
        pad = max(b[2]-b[0], b[3]-b[1]) * 0.2
        self.ax.set_xlim(b[0]-pad, b[2]+pad)
        self.ax.set_ylim(b[1]-pad, b[3]+pad)
        self.fig.canvas.draw_idle()

    def _draw_highlight(self):
        name = self.state.selected.value
        if not name or name not in self.state.design.components:
            return
        comp = self.state.design.components[name]
        try:
            b = comp.qgeometry_bounds()
            from matplotlib.patches import Rectangle
            pad = max(b[2]-b[0], b[3]-b[1]) * 0.05
            rect = Rectangle((b[0]-pad, b[1]-pad),
                              b[2]-b[0]+2*pad, b[3]-b[1]+2*pad,
                              linewidth=2, edgecolor='#FF6B35',
                              facecolor='none', linestyle='--', zorder=10)
            self.ax.add_patch(rect)
        except Exception:
            pass
```

---

## Options form — recursive builder

```python
# utils.py

def set_nested(d, path, value):
    """Set d[path[0]][path[1]]... = value."""
    for key in path[:-1]:
        d = d[key]
    d[path[-1]] = value

def options_to_widgets(opts, path, state, component):
    """Recursively turn a nested options dict into ipywidgets."""
    import ipywidgets as W
    rows = []
    for key, val in opts.items():
        cur_path = path + [key]
        if isinstance(val, dict):
            inner = options_to_widgets(val, cur_path, state, component)
            # ipywidgets 8.x: pass titles= in constructor (set_title() is 7.x API)
            acc = W.Accordion(children=[inner], titles=[key])
            rows.append(acc)
        else:
            parsed = _try_parse(val, state.design)
            value_w  = W.Text(value=str(val), layout=W.Layout(width='150px'))
            parsed_w = W.Label(value=str(parsed),
                               style={'text_color': '#888'},
                               layout=W.Layout(width='100px'))
            def _on_change(change, p=cur_path, pw=parsed_w):
                set_nested(component.options, p, change['new'])
                pw.value = str(_try_parse(change['new'], state.design))
                state.mark_dirty()
            value_w.observe(_on_change, names='value')
            rows.append(W.HBox([
                W.Label(key, layout=W.Layout(width='130px')),
                value_w,
                parsed_w,
            ]))
    return W.VBox(rows)

def _try_parse(val, design):
    try:
        return design.parse_value(str(val))
    except Exception:
        return ''

# NOTE on parse_value units: design.parse_value('10mm') returns 10 (stays in mm).
# Metal's internal unit is mm throughout. Do NOT describe output as metres to the user.
```

---

## Top-level layout assembly

```python
# gui.py
import ipywidgets as W
import matplotlib.pyplot as plt
from .state import GuiState
from .canvas import CanvasPanel
from .panels.component_list import ComponentListPanel
from .panels.options import OptionsPanel
from .panels.library import LibraryPanel
from .panels.variables import VariablesPanel
from .panels.elements import ElementsPanel
from .panels.netlist import NetlistPanel
from .panels.log import LogPanel
from .toolbar import ToolbarRow

def gui(design, height=600, show_log=True, show_library=True, theme='dark'):
    # Never call plt.style.use() here — it is GLOBAL and permanent.
    # Instead pass the style name into CanvasPanel, which applies it via
    # mpl.style.context() scoped to each figure creation and render() call.
    _style = 'dark_background' if theme == 'dark' else 'default'

    state = GuiState(design)
    canvas = CanvasPanel(state, height=height, mpl_style=_style)
    comp_list = ComponentListPanel(state)
    options  = OptionsPanel(state)
    library  = LibraryPanel(state, canvas)
    variables = VariablesPanel(state)
    elements = ElementsPanel(state)
    netlist  = NetlistPanel(state)
    log      = LogPanel(state)
    toolbar  = ToolbarRow(state, canvas)

    left_tabs = W.Tab(
        children=[comp_list.widget, library.widget,
                  variables.widget, log.widget],
        titles=['Components', 'Library', 'Variables', 'Log'],
        layout=W.Layout(width='280px', height=f'{height+40}px')
    )

    right_tabs = W.Tab(
        children=[options.widget],
        titles=['Options'],
        layout=W.Layout(width='320px', height=f'{height+40}px')
    )

    bottom_tabs = W.Tab(
        children=[elements.widget, netlist.widget],
        titles=['Elements', 'Net List'],
        layout=W.Layout(height='220px')
    )

    body = W.HBox(
        [left_tabs, canvas.widget, right_tabs],
        layout=W.Layout(height=f'{height+40}px')
    )

    class MetalGui(W.VBox):
        """Returned widget. Has .close() to detach the log handler."""
        def close(self):
            log.detach()   # removes handler from design.logger
            super().close()

    root = MetalGui(
        [toolbar.widget, body, bottom_tabs],
        layout=W.Layout(border='1px solid #333')
    )

    # Initial render
    canvas.render()

    return root
```

---

## Rebuild flow (end-to-end)

```
User clicks "Rebuild" button
    → toolbar.py: try: design.rebuild()   ← RAISES on component error — must be in try/except
        → on success:
            → canvas.render()
            → comp_list.refresh()
            → elements.refresh()
            → state.mark_clean()
        → on exception:
            pass  # error already written to design.logger → visible in Log panel
                  # dirty flag stays True — button stays orange
```

**Critical:** `design.rebuild()` raises (does not swallow) when any component fails to
build. Verified against the real codebase. A bare call without try/except will crash the
callback and freeze the toolbar button in a broken state.

## Observer double-fire note

When a canvas click triggers `state.select('Q1')`:
1. `state.selected.observe` fires → updates `comp_list.Select.value`
2. `comp_list.Select.observe` fires → calls `state.select('Q1')` again
3. `state.selected.observe` does NOT fire again — `Text.value` is already `'Q1'`

Two fires per user action is expected behavior. The idempotency guard on `state.value`
prevents infinite loops. The extra fire is harmless (a no-op `state.select` call). This
is verified: ipywidgets `Text.observe` only fires when the value actually changes.

---

## GDS export button flow

```
User clicks "Export GDS"
    → toolbar: show filename Text input
    → user types filename, clicks "Go"
    → design.renderers.gds.export_to_gds(filename)
    → Output widget shows: "✓ Exported to filename.gds"
```
