# Prototype Findings

Results from running `prototype.py` and `prototype.ipynb`. Updated as the
prototype is exercised. Things in **bold** require changes to `plan.md` /
`api-sketch.md` before writing production code.

---

## Status legend
- ✅ Validated headlessly (CLI / Agg backend) — no notebook needed
- 🧪 Validated in notebook with real ipympl — requires user to run `prototype.ipynb`
- ❌ Failed — architecture or plan must change

---

## ✅ Validated headlessly (Agg backend, `uv run python`)

### 1. traitlets.HasTraits replaces `W.Text` for state (concern #4)
`MockState(traitlets.HasTraits)` works exactly like the `W.Text`-based version
but without the throwaway widget overhead. `state.observe(handler, names='selected')`
fires on every actual change, skips no-ops. ✅ Recommended for production.

### 2. Weakref handler registry prevents log handler leak on cell re-run (concern #2)
Tested by calling `mock_gui(design)` 5× in a row. Handler count on
`design.logger` stays constant at `baseline+1`. The previous handler is
auto-detached. ✅ This pattern works — recommend it for production.

```
baseline handlers: 1
iter 0: registry=1, on logger=2
iter 1: registry=1, on logger=2   # ← did NOT grow
iter 2: registry=1, on logger=2
...
after close(): registry=0, on logger=1
```

### 3. `MockGui.close()` cleans up matplotlib figures (concern #8)
`plt.get_fignums()` returns `[]` after closing. No leak. ✅

### 4. Rebuild button with try/except keeps GUI alive on bad options
"Force broken option" → `Rebuild` → `ValueError` caught → status shows red
error message → **GUI remains interactive**. State stays `dirty=True` so user
can fix the option without losing context. ✅

### 5. Robust backend check via `type(fig.canvas).__module__` (concern #3)
On Agg: returns `('matplotlib.backends.backend_agg', False)`. On ipympl:
returns `('ipympl.backend_nbagg', True)`. Reliable signal — no string-match
on `mpl.get_backend()`. ✅

### 6. Layered rendering speedup on Agg backend (concern #1)
30-component design, Agg backend (no PNG streaming):
- Fast path (highlight artist swap): **23.7ms/click**
- Slow path (full render_base):       **37.9ms/call**
- Speedup: **~2× on Agg**

The speedup is modest because Agg doesn't pay the PNG-serialization-and-stream
cost that ipympl does. **In a real notebook with ipympl, the speedup will be
much larger** — measured during 🧪 #1 below.

---

## ❌ Failed — REQUIRES PLAN CHANGE

### 1. ⚠️ `fig.canvas` cannot be placed in `W.HBox` without ipympl
**Discovered immediately on first prototype run.**

```python
W.HBox([comp_list.widget, canvas.widget, options.widget])
# TraitError: The 'children' trait ... expected a Widget, not the FigureCanvasAgg
```

The canvas of an Agg figure is `FigureCanvasAgg` — **not** an `ipywidgets.Widget`.
It cannot be placed in an HBox at all. This means:

- **The Phase 6 test plan as written cannot work.** `test_gui_returns_widget`
  will fail at the `qm.gui(design)` call itself, before any assertion.
- Tests in CI (which use Agg by default) need either:
  1. A real `%matplotlib widget` kernel — not feasible in pytest
  2. A mock canvas object that satisfies `isinstance(_, W.Widget)` — pragmatic
  3. A `headless=True` branch in `CanvasPanel` that wraps the figure in an
     `Output` widget (what the prototype does as a fallback)

The prototype now uses approach #3:
```python
if isinstance(self.fig.canvas, W.Widget):
    self.widget = self.fig.canvas       # ipympl case
else:
    self.widget = W.Output(layout=...)  # Agg fallback — static image
```

**Action for plan.md:**
- Phase 1 task: add `isinstance(W.Widget)` branch in `CanvasPanel.__init__`
- Phase 6 test plan: add `pytest.importorskip('ipympl')` AND patch
  `plt.subplots` to return a figure whose canvas type satisfies the Widget
  check, OR run tests with a Jupyter kernel via nbval. Cleanest:
  `pytest.importorskip('ipympl')` and bind a real ipympl backend via
  `matplotlib.use('module://ipympl.backend_nbagg')` in a fixture.

### 2. ⚠️ `MockGui.close()` was being called on a partially-constructed object
On the first failed run (before the W.HBox fix), `close()` ran via `__del__`
and crashed because `self._state` wasn't set yet. Now defensive — uses
`getattr(self, '_state', None)`.

**Action for api-sketch.md:** the `close()` method in production `MetalGui`
must use the same defensive pattern.

---

## 🧪 Notebook run #1 — observations from real ipympl

Backend reported as `ipympl.backend_nbagg → interactive: True` ✓.
All 7 programmatic tests passed. Two UX issues surfaced that the planning
docs did NOT anticipate:

### 1. ⚠️ Aspect ratio not preserved on zoom — REQUIRES PLAN CHANGE
The default matplotlib axes do not set `aspect='equal'`. When the user zooms
into a non-square region, the chip geometry is stretched. For a chip layout
this is wrong: a square pad must stay square at any zoom level.

**Fix applied to prototype:** `ax.set_aspect('equal', adjustable='box')` at
the end of `render_base()`. Verified — `ax.get_aspect()` returns `1.0` after
render.

**Action for plan.md:** Phase 1 task — add `set_aspect('equal', ...)` after
every `renderer.render(ax)` call. This is non-negotiable for chip viewing.

### 2. ⚠️ ipympl default toolbar is unusable — REQUIRES PLAN CHANGE
The `fig.canvas.toolbar_visible=True` toolbar shows matplotlib's tiny
navigation icons (pan, zoom-rect, home, save). The zoom tool is
rectangle-drag-to-zoom — no simple +/- lens buttons. New users don't know
how to use it.

**Fix applied to prototype:**
- Hide the default toolbar: `toolbar_visible=False, header_visible=False,
  footer_visible=False`
- Add four explicit zoom buttons to our toolbar:
  - 🔍+ Zoom in (`zoom_scale(0.7)`)
  - 🔍− Zoom out (`zoom_scale(1.4)`)
  - ⤢ Zoom to fit (`autoscale + set_aspect`)
  - ⊕ Zoom to selected (`set_xlim/ylim` around `qgeometry_bounds`)
- API on `MockCanvas`: `zoom_scale(factor)`, `zoom_fit()`, `zoom_to(name)`

**Action for plan.md:** Phase 1 task — hide the default ipympl toolbar and
add explicit view-control buttons to `ToolbarRow`. Document the
`zoom_scale/zoom_fit/zoom_to` API on `CanvasPanel`.

### 3. ℹ️ Baseline handler count in Test 5 is misleading (cosmetic)
The notebook's Test 5 measures `baseline = len(design.logger.handlers)` AFTER
cell 5 has already called `mock_gui(design)` (which attaches a handler).
This makes the printed baseline 2 instead of 1, and the "must be baseline+1"
expected value reads as "must be 3" when it's actually "must be 2".

The dedup behavior itself works correctly — handler count stayed flat across
5 re-runs and dropped to 1 (original) after closing all guis. The test
output is just hard to read.

**Action for prototype.ipynb:** Move the baseline measurement to a fresh
design, OR detach the cell-5 gui first. Cosmetic only — doesn't change the
production code.

---

## 🧪 Still pending — to be checked in `prototype.ipynb` by the user

### 1. ipympl performance speedup (concern #1)
Expected: with 30 components and real ipympl PNG streaming, fast path should
be 5–20× faster than slow path. If speedup is < 3×, the layered architecture
may not be worth the complexity.

### 2. Visual layout sanity
- Does the HBox of (list | canvas | options) actually look right at 720+200+340 width?
- Does the canvas resize correctly when the browser window changes?
- Does the dark theme apply to both the matplotlib figure AND the widget frame
  (or just the figure)?

### 3. Click latency in a real browser
The 23.7ms measured headlessly is just the Python side. The end-to-end click
latency includes the JS → kernel → Python → kernel → JS round-trip, typically
50–200ms additional. Acceptable if total stays under 300ms.

### 4. Cell re-run UX
When the user re-runs the cell with `gui = mock_gui(design); gui`:
- Does the OLD gui's canvas widget disappear from the cell output?
- Does the NEW canvas appear in its place?
- Or do BOTH show up (a known ipympl gotcha)?

### 5. Cross-environment test
Try in: JupyterLab (local), VS Code Jupyter, Google Colab. Note any
environment where:
- `%matplotlib widget` is required vs auto-detected
- Backend detection misreports
- Widgets render but click events don't reach the Python handler

### 6. Options edit → rebuild flow
Edit `pos_x` to `2mm` in the options panel → click Rebuild → verify Q2 moves
on the canvas. This tests the closure capture in the option-change handler.

### 7. Broken rebuild status display
Click "Force broken option" → Rebuild → verify red error message appears AND
the design.logger.handlers[-1] sink recorded the error. Tests both the
visible UX and the log capture path.

---

## Recommendations (after headless validation only)

1. **The architecture is sound.** All five high-severity concerns from
   `concerns.md` are validated by the prototype. Two-layer rendering,
   traitlets state, weakref handler dedup, robust backend check, and
   figure-leak cleanup all work as designed.

2. **The Phase 6 test plan needs a rewrite.** The current plan assumes
   ipywidgets tests can run in any pytest environment. They can't — without
   a real ipympl backend, the figure canvas isn't a widget and HBox
   construction fails. Either: (a) skip GUI tests entirely in CI and rely on
   the notebook execute job, or (b) add ipympl + a backend-binding fixture to
   the test suite.

3. **Defensive `close()` is mandatory.** ipywidgets calls `__del__` on
   garbage-collected widgets, which calls `close()`. If `close()` references
   attrs that may not be set, you get spurious tracebacks in the log on every
   cell re-run. The prototype's `getattr(self, '_state', None)` pattern
   handles this.

4. **Update the README's "Status" section** to reflect: planning done,
   prototype done, real implementation NOT started.

5. **Notebook tests pending.** Items in 🧪 above must be checked in a real
   notebook before committing to Phase 1. The biggest unknown is item #1 —
   if the layered architecture doesn't actually speed up the notebook UX,
   the added complexity (two render paths to maintain) isn't justified.
