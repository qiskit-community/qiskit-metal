# Deeper Architectural Concerns

The first three red team passes were tactical — fixing bugs in code I'd already
proposed. This pass questions the **architecture itself**. The goal is to surface
issues that a working implementation will hit and we cannot fix without redesign.

Severity rubric:
- **🔴 High** — blocks implementation or causes a UX problem we cannot patch around
- **🟡 Medium** — causes friction, maintenance pain, or technical debt
- **🟢 Low** — nice-to-have, can be deferred to Tier 2

---

## 🔴 1. Canvas re-render on every selection is the wrong design

**Current plan:** Every selection change calls `canvas.render()` which does
`ax.cla()` → full `QMplRenderer.render(ax)` → redraw all geometry → add highlight rect.

**The problem:**
- `QMplRenderer.render()` is the slow path. It iterates all components, builds
  shapely → matplotlib patches, applies styles. The docs note ~100ms–2s for 50
  components. **Every click triggers this.**
- A real user clicks 10× to inspect components. That's 1–20 seconds of waiting,
  in a UI where they expect <50ms feedback.
- ipympl re-streams the rendered PNG to the browser on each redraw, so even if
  matplotlib were fast, the network round-trip adds latency.

**The fix is structural:** split into two layers.
- **Base layer:** rendered once at `gui()` start and after `rebuild`. Cached.
- **Highlight layer:** a separate matplotlib `Artist` (Rectangle patch added/
  removed). Selection change only adds/removes this one artist — no `ax.cla()`.

```python
class CanvasPanel:
    def __init__(self, ...):
        self._highlight_patch = None  # the orange rectangle

    def render_base(self):
        """Slow path — full re-render. Called on rebuild only."""
        self.ax.cla()
        self.renderer.render(self.ax)
        self._highlight_patch = None  # cleared by ax.cla()
        self._refresh_highlight()
        self.fig.canvas.draw_idle()

    def _refresh_highlight(self):
        """Fast path — add/remove one Rectangle. Called on selection change."""
        if self._highlight_patch is not None:
            self._highlight_patch.remove()
            self._highlight_patch = None
        name = self.state.selected.value
        if name and name in self.state.design.components:
            b = self.state.design.components[name].qgeometry_bounds()
            from matplotlib.patches import Rectangle
            pad = max(b[2]-b[0], b[3]-b[1]) * 0.05
            self._highlight_patch = Rectangle(
                (b[0]-pad, b[1]-pad), b[2]-b[0]+2*pad, b[3]-b[1]+2*pad,
                linewidth=2, edgecolor='#FF6B35', facecolor='none',
                linestyle='--', zorder=10)
            self.ax.add_patch(self._highlight_patch)
        self.fig.canvas.draw_idle()
```

**Action:** Update `api-sketch.md` and `plan.md` to use this two-layer approach.

---

## 🔴 2. Log handler attachment timing leaks

**Current plan:** `LogPanel` attaches a `logging.Handler` to `design.logger` in
`__init__`. `MetalGui.close()` detaches it.

**The problem:**
- `qm.gui(design)` constructs the widget but **may not display it**. If the user
  does `g = qm.gui(design)` and then never displays `g`, the handler is attached
  forever. The design now has a handler pointing to an invisible Output widget.
  On cell re-run: another handler attaches. Logs duplicate.
- ipywidgets does NOT reliably notify us on widget destroy. There's no `__del__`
  guarantee with reference cycles (and the observer pattern creates cycles).
- Even with explicit `close()`, users will forget to call it.

**The fix:** Attach the handler in `_ipython_display_`, detach in a teardown
hook. Or simpler: keep a bounded ring buffer of recent log records on the GUI
object, and read from it lazily when the log panel is displayed.

```python
class LogPanel:
    """Polls design.logger via a ring buffer — no persistent handler attached."""
    def __init__(self, state, max_records=500):
        from collections import deque
        self._buffer = deque(maxlen=max_records)
        self._handler = _RingBufferHandler(self._buffer)
        state.design.logger.addHandler(self._handler)
        # ... but still need detach. There is no clean answer here.
```

**The real fix:** accept that this needs `close()`. Document loudly. Make
`gui()` print "Call gui.close() before re-running this cell" the second time
it's called against the same design. Detect via a weakref registry keyed on
`id(design)`.

**Action:** Add a `_handler_registry` weakref dict at module level. `gui()`
checks if `design` already has an active handler from a previous gui and
auto-detaches it. This handles the cell-rerun case without user action.

---

## 🔴 3. ipympl backend detection is fragile

**Current plan:** Check `mpl.get_backend()` for `'ipympl'` or `'widget'`.

**The problem:**
- VS Code Jupyter reports backend as `'inline'` even when widgets work via VSCode's
  own widget infrastructure.
- `%matplotlib widget` is a magic that some users put in the cell AFTER importing
  matplotlib. By then the backend is set; further changes have no effect.
- Some JupyterLab installs report backend as
  `'module://matplotlib_inline.backend_inline'` even when ipympl is installed.

**The robust pattern:** Don't trust `get_backend()`. Try to create the figure,
then check the canvas type at runtime:

```python
def _check_interactive_canvas():
    import matplotlib.pyplot as plt
    fig = plt.figure()
    canvas_module = type(fig.canvas).__module__
    plt.close(fig)
    is_ipympl = 'ipympl' in canvas_module
    is_widget = 'widget' in canvas_module
    return is_ipympl or is_widget
```

Even this is imperfect — some envs require a kernel restart after installing
ipympl. The error message must say so explicitly.

**Action:** Replace string-match on `get_backend()` with canvas-module check
in `dependencies.md` and the actual implementation.

---

## 🟡 4. State stored in `ipywidgets.Text` is semantically wrong

**Current plan:** `GuiState.selected = W.Text(value='')` — use a Text widget as
a reactive trait holder.

**The problem:**
- Text is a UI widget — it has weight, layout, model props we don't use.
- A `GuiState` instance creates 2 invisible widgets that get serialized to the
  frontend even though they're never displayed.
- Confusing for new contributors: "why is the state a textbox?"

**The fix:** Use `traitlets.HasTraits` (already a dep — comes with ipywidgets).

```python
import traitlets

class GuiState(traitlets.HasTraits):
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

# Panels observe with the same .observe() API — no other changes needed.
```

This is a 10-line refactor with zero downside.

**Action:** Update `api-sketch.md` to use `traitlets.HasTraits`.

---

## 🟡 5. `discover_components()` blocks for 1–3s on first call

**Current plan:** `pkgutil.walk_packages` over `qiskit_metal.qlibrary` at first
`qm.gui()` call. Cached afterwards.

**The problem:**
- First call to `qm.gui(design)` blocks the kernel for 1–3s with no feedback.
- Discovery imports every qlibrary submodule. Some import optional deps
  (gmsh, pyaedt). Even with try/except, the import attempt is slow.
- `sys.modules` grows by ~50 entries permanently.

**The fix:** Make discovery lazy — populate Library tab progressively.

- Library tab shows "Loading components..." immediately.
- Background discovery runs in a thread (or via `IPython.display.display`'s
  async support).
- Each discovered component is appended to the Select widget as it's found.

This is real work. For Tier 1 the blocking 1–3s on first call is acceptable —
just add a "Discovering components..." Label that's removed when done. Use
`Output.capture()` to make it visible.

**Action:** Document the blocking behavior. Add a loading indicator. Defer
async discovery to Tier 2.

---

## 🟡 6. Cloud filesystem asymmetry

**Current plan:** Save Design / Export GDS buttons write to local filesystem.

**The problem:**
- In Colab/Binder, the filesystem is ephemeral. Files vanish when the kernel
  dies. Users save a `.metal.py` file and never see it again.
- Users in these envs need a **download link**, not a file path.

**The fix:** After every save/export, also display an `IPython.display.FileLink`:

```python
def _on_save(filename):
    design.to_python_script(filename)
    from IPython.display import FileLink, display
    display(FileLink(filename, result_html_prefix="✓ Saved — click to download: "))
```

In Colab, this gives users a download link. Locally, it's just a file path
link — still useful.

Also: **add Load Design**. Currently the plan has no load — just save. That's a
glaring asymmetry. At minimum show a code snippet users can copy:
```
# To load, run this in a new cell:
exec(open('mydesign.metal.py').read())
```

**Action:** Add `FileLink` to save/export handlers. Add "Load" button that
shows the exec snippet.

---

## 🟡 7. The `gui()` returning a widget directly is OK but locks the API

**Current plan:** `qm.gui(design) → ipywidgets.VBox` subclass (`MetalGui`).
User does `display(gui)` or `gui` to render.

**The problem:**
- Returning a widget means the public API is the widget tree. Users who try
  `gui.canvas` or `gui.state` would be poking at private implementation.
- We can never add a non-widget feature (e.g., `gui.to_html()` for export)
  without it being a method on the VBox subclass, which is awkward.

**Alternative:** Return a controller object with `.widget` property:
```python
g = qm.gui(design)
display(g.widget)  # explicit — more verbose
g.select('Q1')     # methods are first-class
g.close()
```

**Tradeoff:** Lose the `display(gui)` ergonomics. Gain a cleaner API.

**Decision:** Stick with the subclass approach (`MetalGui(VBox)`) — Jupyter
users expect `display(g)` to just work. Add `.select()`, `.refresh()`,
`.close()` as methods on the subclass. The widget IS the API.

**Action:** Document this decision in `api-sketch.md`. Note it's intentional,
not laziness.

---

## 🟡 8. matplotlib figure leak on cell re-run

**Current plan:** `gui()` calls `plt.subplots()`. `close()` doesn't call
`plt.close(fig)`.

**The problem:** matplotlib keeps a global registry of figures (`plt.gcf()`
history). Each cell re-run creates a new figure that's never closed. After 50
re-runs the user has 50 figures in memory — multi-MB each for a complex chip.

**The fix:** `MetalGui.close()` must call `plt.close(self.canvas.fig)`.

**Action:** One-line addition to `close()` in `api-sketch.md`.

---

## 🟢 9. Live options updates (defer to Tier 2)

Modern UIs update on every keystroke (debounced). Our Rebuild button is the
MetalGUI pattern — explicit, simple, but old-fashioned. Tier 2 should add a
500ms-debounced live update mode.

---

## 🟢 10. Component icons in library (defer to Tier 2)

PNG thumbnails for each component would be a big UX improvement. Out of scope
for Tier 1.

---

## What I previously got wrong

Things from passes 1–2 that this pass surfaces as deeper problems:

1. **Pass 1 fix for `_draw_highlight()`** assumed it's cheap to call inside
   `render()`. It is — but `render()` itself is not cheap. The fix in concern #1
   above supersedes the Pass 1 approach.

2. **Pass 2 `mpl.style.context()` wrapping `render()`**: each render now enters
   a style context. This is correct but adds ~1ms overhead per render — fine
   for explicit rebuild, but if combined with the layer fix in #1, the
   highlight refresh path doesn't need the style context (it only adds a
   Rectangle whose colors we hard-code).

3. **The `[notebook]` extra name**: pyproject.toml already has a `[dependency-
   groups] jupyter` block. We're adding `[project.optional-dependencies]
   notebook`. The names are similar but the mechanisms are completely
   different. This may confuse users. Consider naming the extra `[jupyter-gui]`
   to be unambiguous, at the cost of typing more.

---

## Recommended next step: build a mock prototype

The planning docs are now ~1000 lines. Every additional review pass yields
diminishing returns because we're reasoning about code we haven't written.

**The cheapest way to find the remaining problems is to build a 200–300 line
prototype** in `_dev/jupyter_gui/prototype.py` + `_dev/jupyter_gui/prototype.ipynb`
that exercises the critical paths:

### Prototype scope (single file, throwaway code)

1. `MockState(traitlets.HasTraits)` — concern #4 validation
2. `MockCanvas`:
   - Real `QMplRenderer` integration
   - Two-layer rendering (concern #1 validation)
   - Click → selection works
3. `MockOptionsPanel`:
   - One editable field per top-level option key (no recursion)
   - `state.dirty` toggle on edit
4. `MockToolbar`:
   - Rebuild button with try/except (concern in Pass 3)
   - "Force broken" button — sets bad options to test error path
5. `mock_gui(design)` function:
   - Lazy import pattern (concern #2 timing for log handler)
   - Returns a `MockGui(VBox)` with `.close()` that calls `plt.close()`
   - Backend check via canvas-type (concern #3)

### What the prototype validates

| Concern | How prototype tests it |
|---------|------------------------|
| #1 Render performance | Click 10× rapidly. Measure highlight latency. |
| #2 Log handler leak | Re-run cell 5×. Check `design.logger.handlers` count. |
| #3 Backend fragility | Run in JupyterLab, VS Code, and `%matplotlib inline` |
| #4 traitlets vs Text | Code is cleaner — subjective but visible |
| #6 FileLink | Click Save in `prototype.ipynb`. Verify download link appears. |
| #8 Figure leak | Re-run 5×, check `plt.get_fignums()` count |
| Layout sanity | Visual — does the HBox actually look right? |

### What the prototype does NOT need

- All 7 panels (just canvas + 1 options field + toolbar)
- Library browser
- Recursive options editor
- Theme switching
- GDS export
- Pretty styling

### Time estimate

~2–3 hours to write. Yields high-confidence answers to questions that 10 more
pages of planning cannot answer.

### Deliverable

- `_dev/jupyter_gui/prototype.py` — 200–300 lines
- `_dev/jupyter_gui/prototype.ipynb` — 10 cells exercising the prototype
- `_dev/jupyter_gui/prototype-findings.md` — what worked, what didn't, what
  the full implementation needs to change vs the current plan

If findings show the architecture is sound: proceed with Phase 1 confidently.
If findings expose deeper issues: revise the plan **before** writing 2000
lines of production code.
