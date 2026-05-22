"""Mock prototype for qm.gui() — throwaway code for architecture validation.

NOT for production. NOT importable from qiskit_metal. Lives in _dev/.

This prototype validates the architectural decisions in concerns.md:
- 🔴 #1  Two-layer canvas (slow base + fast highlight) — render_base() vs _refresh_highlight()
- 🔴 #2  Log handler dedup via weakref-finalized registry — handles cell re-runs
- 🔴 #3  Robust backend check via type(fig.canvas).__module__ — not get_backend() string-match
- 🟡 #4  traitlets.HasTraits for state — not W.Text wrappers
- 🟡 #7  MetalGui(VBox) subclass with .select()/.refresh()/.close() methods
- 🟡 #8  plt.close(fig) on teardown — prevent figure registry leak

To run: open prototype.ipynb in a Jupyter env with ipywidgets+ipympl installed
       (e.g. `uv run --with ipywidgets --with ipympl jupyter lab`)
"""

import logging
import weakref

import ipywidgets as W
import matplotlib as mpl
import matplotlib.pyplot as plt
import traitlets
from matplotlib.patches import Rectangle

from qiskit_metal.renderers.renderer_mpl.mpl_renderer import QMplRenderer


# ---------------------------------------------------------------------------
# Module-level log handler registry — concern #2
# ---------------------------------------------------------------------------
# Maps id(design) → handler. When mock_gui() is re-called on the same design
# (e.g. cell re-run), we detach the previous handler before attaching a new
# one. weakref.finalize cleans the entry when the design is garbage collected.
_active_handlers: dict = {}


def _register_handler(design, handler):
    key = id(design)
    old = _active_handlers.pop(key, None)
    if old is not None:
        try:
            design.logger.removeHandler(old)
        except Exception:
            pass
    _active_handlers[key] = handler
    weakref.finalize(design, _active_handlers.pop, key, None)


def _unregister_handler(design):
    handler = _active_handlers.pop(id(design), None)
    if handler is not None:
        try:
            design.logger.removeHandler(handler)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Backend detection — concern #3
# ---------------------------------------------------------------------------
def check_interactive_backend():
    """Returns (is_interactive: bool, canvas_module_name: str).

    Robust: creates an actual figure and inspects the canvas class module
    rather than trusting mpl.get_backend() (which lies in VS Code, etc).
    """
    fig = plt.figure()
    canvas_module = type(fig.canvas).__module__
    plt.close(fig)
    ok = 'ipympl' in canvas_module or 'widget' in canvas_module.lower()
    return ok, canvas_module


# ---------------------------------------------------------------------------
# State — concern #4
# ---------------------------------------------------------------------------
class MockState(traitlets.HasTraits):
    """Reactive state via traitlets directly — no W.Text wrappers."""

    selected = traitlets.Unicode('')
    dirty = traitlets.Bool(False)

    def __init__(self, design):
        super().__init__()
        self.design = design

    def select(self, name):
        self.selected = name or ''

    def mark_dirty(self):
        self.dirty = True

    def mark_clean(self):
        self.dirty = False


# ---------------------------------------------------------------------------
# Canvas — concern #1 (two-layer rendering)
# ---------------------------------------------------------------------------
class MockCanvas:
    """Two-layer canvas:
      - render_base(): SLOW — full re-render via QMplRenderer. Called on rebuild only.
      - _refresh_highlight(): FAST — adds/removes one Rectangle artist. Called on click.
    """

    def __init__(self, state, height=500, mpl_style='dark_background'):
        self.state = state
        self.renderer = QMplRenderer(design=state.design)
        self._style = mpl_style
        self._highlight_patch = None

        with mpl.style.context(self._style):
            self.fig, self.ax = plt.subplots(figsize=(7, height / 100))

        # Hide the default ipympl toolbar — the tiny matplotlib nav icons are
        # confusing for non-matplotlib users. We provide our own zoom/fit
        # buttons in MockToolbar (larger, labeled, clearer affordance).
        for attr, val in [('toolbar_visible', False),
                          ('header_visible', False),
                          ('footer_visible', False)]:
            try:
                setattr(self.fig.canvas, attr, val)
            except AttributeError:
                pass

        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

        # FINDING: fig.canvas is only an ipywidgets.Widget when ipympl backend
        # is active. On Agg (CI/headless) it's FigureCanvasAgg which CANNOT be
        # placed in an HBox. Fall back to wrapping the static figure in Output.
        if isinstance(self.fig.canvas, W.Widget):
            self.widget = self.fig.canvas
        else:
            self.widget = W.Output(
                layout=W.Layout(width='720px', height=f'{height}px'))
            # No display() yet — render_base() will populate

        # Fast-path highlight on selection change (no full re-render)
        state.observe(self._on_selection_change, names='selected')

    def render_base(self):
        """SLOW PATH — call only on rebuild."""
        with mpl.style.context(self._style):
            self.ax.cla()
            self.renderer.render(self.ax)
            # Chip geometry MUST preserve aspect ratio. adjustable='box' lets
            # the axes box shrink/grow to accommodate xlim/ylim without
            # distorting the data. Without this, zooming a non-square region
            # stretches the chip.
            self.ax.set_aspect('equal', adjustable='box')
            self._highlight_patch = None  # cleared by ax.cla()
            self._refresh_highlight()
        self.fig.canvas.draw_idle()

    def zoom_scale(self, factor):
        """Zoom in (<1) or out (>1) about the current view center."""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        cx, cy = (xlim[0] + xlim[1]) / 2, (ylim[0] + ylim[1]) / 2
        w = (xlim[1] - xlim[0]) * factor / 2
        h = (ylim[1] - ylim[0]) * factor / 2
        self.ax.set_xlim(cx - w, cx + w)
        self.ax.set_ylim(cy - h, cy + h)
        self.fig.canvas.draw_idle()

    def zoom_fit(self):
        """Autoscale to show everything."""
        self.ax.autoscale()
        self.ax.set_aspect('equal', adjustable='box')
        self.fig.canvas.draw_idle()

    def zoom_to(self, name, pad_frac=0.3):
        """Zoom to a named component."""
        if name not in self.state.design.components:
            return
        try:
            b = self.state.design.components[name].qgeometry_bounds()
        except Exception:
            return
        pad = max(b[2] - b[0], b[3] - b[1]) * pad_frac
        self.ax.set_xlim(b[0] - pad, b[2] + pad)
        self.ax.set_ylim(b[1] - pad, b[3] + pad)
        self.fig.canvas.draw_idle()

    def _on_selection_change(self, change):
        """FAST PATH — only touches the highlight artist."""
        self._refresh_highlight()
        self.fig.canvas.draw_idle()

    def _refresh_highlight(self):
        if self._highlight_patch is not None:
            try:
                self._highlight_patch.remove()
            except (ValueError, AttributeError):
                pass
            self._highlight_patch = None

        name = self.state.selected
        if not name or name not in self.state.design.components:
            return
        comp = self.state.design.components[name]
        try:
            b = comp.qgeometry_bounds()
        except Exception:
            return
        pad = max(b[2] - b[0], b[3] - b[1]) * 0.05
        self._highlight_patch = Rectangle(
            (b[0] - pad, b[1] - pad),
            b[2] - b[0] + 2 * pad,
            b[3] - b[1] + 2 * pad,
            linewidth=2, edgecolor='#FF6B35',
            facecolor='none', linestyle='--', zorder=10)
        self.ax.add_patch(self._highlight_patch)

    def _on_click(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return
        x, y = event.xdata, event.ydata
        best, best_dist = None, float('inf')
        for name, comp in self.state.design.components.items():
            try:
                b = comp.qgeometry_bounds()
                cx = (b[0] + b[2]) / 2
                cy = (b[1] + b[3]) / 2
                d = (x - cx) ** 2 + (y - cy) ** 2
                if d < best_dist:
                    best_dist = d
                    best = name
            except Exception:
                pass
        if best:
            self.state.select(best)

    def close(self):
        plt.close(self.fig)


# ---------------------------------------------------------------------------
# Component list — minimal
# ---------------------------------------------------------------------------
class MockComponentList:
    def __init__(self, state):
        self.state = state
        names = list(state.design.components.keys())
        self.select_w = W.Select(
            options=names, value=names[0] if names else None,
            layout=W.Layout(width='200px', height='220px'))
        self.select_w.observe(self._on_select, names='value')
        state.observe(self._on_state, names='selected')
        self.widget = W.VBox([W.HTML("<b>Components</b>"), self.select_w])

    def _on_select(self, change):
        if change['new'] is not None:
            self.state.select(change['new'])

    def _on_state(self, change):
        name = change['new']
        # Guard: only update if value differs (prevents redundant fire)
        if name and name != self.select_w.value and name in self.select_w.options:
            self.select_w.value = name

    def refresh(self):
        self.select_w.options = list(self.state.design.components.keys())


# ---------------------------------------------------------------------------
# Options panel — minimal (one Text per top-level scalar key, no recursion)
# ---------------------------------------------------------------------------
class MockOptionsPanel:
    def __init__(self, state):
        self.state = state
        self.header = W.HTML("<b>Options</b><br><i>(select a component)</i>")
        self.container = W.VBox([])
        self.widget = W.VBox([self.header, self.container],
                              layout=W.Layout(width='340px'))
        state.observe(self._on_selection, names='selected')

    def _on_selection(self, change):
        name = change['new']
        if not name or name not in self.state.design.components:
            self.header.value = "<b>Options</b><br><i>(select a component)</i>"
            self.container.children = ()
            return
        comp = self.state.design.components[name]
        self.header.value = f"<b>Options — {name}</b>"

        rows = []
        for key, val in comp.options.items():
            if isinstance(val, dict):
                continue  # prototype: skip nested
            text = W.Text(value=str(val),
                          layout=W.Layout(width='160px'))
            row = W.HBox([
                W.Label(key, layout=W.Layout(width='140px')),
                text,
            ])
            # Closure: capture key + comp via default args (correct pattern)
            def _on_change(change, k=key, c=comp):
                c.options[k] = change['new']
                self.state.mark_dirty()
            text.observe(_on_change, names='value')
            rows.append(row)
        self.container.children = rows


# ---------------------------------------------------------------------------
# Toolbar — Rebuild with try/except + Force-broken to test error path
# ---------------------------------------------------------------------------
class MockToolbar:
    def __init__(self, state, canvas, comp_list):
        self.state = state
        self.canvas = canvas
        self.comp_list = comp_list

        self.rebuild_btn = W.Button(description="Rebuild", icon='refresh')
        self.break_btn = W.Button(description="Force broken option",
                                   button_style='warning')
        self.status = W.HTML("")

        # View controls — clearer than matplotlib's tiny default toolbar.
        # FontAwesome 4 icons; tooltip shows on hover.
        btn_layout = W.Layout(width='36px', padding='0')
        self.zoom_in_btn = W.Button(icon='search-plus', tooltip='Zoom in',
                                     layout=btn_layout)
        self.zoom_out_btn = W.Button(icon='search-minus', tooltip='Zoom out',
                                      layout=btn_layout)
        self.fit_btn = W.Button(icon='expand', tooltip='Zoom to fit',
                                 layout=btn_layout)
        self.focus_btn = W.Button(icon='crosshairs',
                                   tooltip='Zoom to selected component',
                                   layout=btn_layout)

        self.rebuild_btn.on_click(self._on_rebuild)
        self.break_btn.on_click(self._on_break)
        self.zoom_in_btn.on_click(lambda _: canvas.zoom_scale(0.7))
        self.zoom_out_btn.on_click(lambda _: canvas.zoom_scale(1.4))
        self.fit_btn.on_click(lambda _: canvas.zoom_fit())
        self.focus_btn.on_click(lambda _: canvas.zoom_to(state.selected))

        state.observe(self._on_dirty, names='dirty')

        # Group with a visual separator (Label spacer)
        view_group = W.HBox([self.zoom_in_btn, self.zoom_out_btn,
                              self.fit_btn, self.focus_btn])
        self.widget = W.HBox([
            self.rebuild_btn, self.break_btn,
            W.Label('  |  '), view_group,
            W.Label('  '), self.status,
        ])

    def _on_rebuild(self, _btn):
        try:
            self.state.design.rebuild()
            self.canvas.render_base()
            self.comp_list.refresh()
            self.state.mark_clean()
            self.status.value = "<span style='color:#0a0'>✓ Rebuild OK</span>"
        except Exception as e:
            # Error is also written to design.logger by rebuild() itself
            msg = f"{type(e).__name__}: {str(e)[:80]}"
            self.status.value = f"<span style='color:#d00'>✗ {msg}</span>"

    def _on_break(self, _btn):
        name = self.state.selected
        if not name or name not in self.state.design.components:
            self.status.value = "<span style='color:#fa0'>Select a component first</span>"
            return
        self.state.design.components[name].options['pad_width'] = 'INVALID_UNIT'
        self.state.mark_dirty()
        self.status.value = "<span style='color:#fa0'>Bad option set — click Rebuild</span>"

    def _on_dirty(self, change):
        if change['new']:
            self.rebuild_btn.button_style = 'warning'
            self.rebuild_btn.description = "Rebuild (needed)"
        else:
            self.rebuild_btn.button_style = ''
            self.rebuild_btn.description = "Rebuild"


# ---------------------------------------------------------------------------
# Top-level GUI — subclass VBox so display(gui) works AND methods work
# ---------------------------------------------------------------------------
class MockGui(W.VBox):
    def __init__(self, state, canvas, comp_list, options, toolbar):
        body = W.HBox([comp_list.widget, canvas.widget, options.widget])
        super().__init__([toolbar.widget, body])
        self._state = state
        self._canvas = canvas
        self._comp_list = comp_list
        self._options = options
        self._toolbar = toolbar

    def select(self, name):
        self._state.select(name)

    def refresh(self):
        self._canvas.render_base()

    def close(self):
        # Defensive: __init__ may have failed before attrs were set
        state = getattr(self, '_state', None)
        canvas = getattr(self, '_canvas', None)
        if state is not None:
            _unregister_handler(state.design)
        if canvas is not None:
            canvas.close()
        super().close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
class _PrototypeLogHandler(logging.Handler):
    """Captures records into a list for inspection. Real impl writes to Output."""
    def __init__(self, sink):
        super().__init__()
        self.sink = sink

    def emit(self, record):
        self.sink.append(self.format(record))


def mock_gui(design, height=500, attach_log_handler=True):
    """Build the prototype GUI.

    The real qm.gui() will be a lazy wrapper in qiskit_metal/__init__.py that
    does this import inside the function body. Here we import at module level
    for prototyping convenience.
    """
    ok, canvas_module = check_interactive_backend()
    if not ok:
        print(f"⚠ Backend: '{canvas_module}' is not interactive.")
        print("  In a notebook, add `%matplotlib widget` in a cell ABOVE this one.")
        print("  Continuing — the figure will be static (no click events).")

    if attach_log_handler:
        log_sink: list = []
        handler = _PrototypeLogHandler(log_sink)
        _register_handler(design, handler)
        design.logger.addHandler(handler)

    state = MockState(design)
    canvas = MockCanvas(state, height=height)
    comp_list = MockComponentList(state)
    options = MockOptionsPanel(state)
    toolbar = MockToolbar(state, canvas, comp_list)

    gui = MockGui(state, canvas, comp_list, options, toolbar)
    if attach_log_handler:
        gui._log_sink = log_sink  # exposed for prototype inspection

    canvas.render_base()
    names = list(design.components.keys())
    if names:
        state.select(names[0])

    return gui
