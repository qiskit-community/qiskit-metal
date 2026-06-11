# Implementation Plan

Target: `qm.gui(design)` — a Jupyter-native GUI widget, no Qt required.
Target release: **v0.7.0**.
Code lives at: `src/qiskit_metal/jupyter_gui/`

You test at the end of each phase using the demo notebook:
`_dev/jupyter_gui/demo.ipynb`

---

## Phase 0 — Setup (before any code)

**Tasks:**
- [ ] Checkout dev branch (`claude/v0.7.0-lite-flip-and-rebrand` or new branch off it)
- [ ] Create `src/qiskit_metal/jupyter_gui/__init__.py` (empty, just `from .gui import gui`)
- [ ] Create `src/qiskit_metal/jupyter_gui/` folder structure (all files empty stubs)
- [ ] Add lazy `gui()` wrapper to `src/qiskit_metal/__init__.py` (see `dependencies.md` for
  the exact pattern — import inside the function body, not at module level; error message
  must say `pip install 'quantum-metal[notebook]'`, not `[gui]`)
- [ ] Add `[notebook]` extra to `pyproject.toml` (do NOT touch `[gui]` — that's PySide6):
  ```toml
  [project.optional-dependencies]
      notebook = ["ipywidgets>=8.0", "ipympl>=0.9"]   # NEW — add after existing gui line
  ```
  Also add `"ipywidgets>=8.0", "ipympl>=0.9"` to the `full` extra list.
- [ ] Add `_dev/jupyter_gui/demo.ipynb` as the test notebook
- [ ] Confirm: `import qiskit_metal as qm; qm.gui` resolves without error (even without
  ipywidgets installed — should not raise at import time)

**You test:** `import qiskit_metal as qm; print(qm.gui)` → should print something.

---

## Phase 1 — Layout scaffold + canvas (Days 1–2)

**Goal:** `qm.gui(design)` returns a visible widget with the correct layout.
Canvas renders the design. No interactions yet.

**Tasks:**
- [ ] `state.py` — `GuiState` class with `selected` and `dirty` traits
- [ ] `canvas.py` — `CanvasPanel`:
  - Creates ipympl figure + axes
  - `render()` calls `QMplRenderer(design=design).render(ax)` + `draw_idle()`
  - Returns `self.widget = fig.canvas`
- [ ] `panels/component_list.py` — stub `ipywidgets.Select` (empty for now)
- [ ] `panels/options.py` — stub `ipywidgets.Label("Select a component")`
- [ ] `panels/library.py` — stub
- [ ] `panels/variables.py` — stub
- [ ] `panels/elements.py` — stub
- [ ] `panels/netlist.py` — stub
- [ ] `panels/log.py` — stub
- [ ] `toolbar.py` — `ToolbarRow` with just "Rebuild" and "Zoom to fit" buttons wired up
- [ ] `gui.py` — assemble the full layout (see `api-sketch.md`)

**You test (demo.ipynb cell 1):**
```python
import qiskit_metal as qm
from qiskit_metal import designs, Dict
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

design = designs.DesignPlanar()
TransmonPocket(design, 'Q1', options=Dict(connection_pads=Dict(a=Dict())))
gui = qm.gui(design)
gui
```
Expected: layout appears, chip renders in centre canvas, "Rebuild" button visible.

---

## Phase 2 — Component selection (Days 3–4)

**Goal:** Click a component on the canvas → it highlights, the component
list selects it, the options panel shows its name.

**Tasks:**
- [ ] `canvas.py` — `mpl_connect('button_press_event', _on_click)`
  - `_find_nearest_component(x, y)` by centroid distance
  - On click: `state.select(name)`
- [ ] `canvas.py` — `_draw_highlight()` — orange dashed rectangle around selected component
  - Called at end of every `render()`
- [ ] `state.py` — `selected.observe` → trigger `canvas.render()`
  - (So highlight redraws when selection changes from list too)
- [ ] `panels/component_list.py` — populate `Select` from `design.components`
  - `.observe('value')` → `state.select(change['new'])`
  - `state.selected.observe(...)` → update `Select.value` (bidirectional)
- [ ] `panels/component_list.py` — "Zoom to" button → `canvas.zoom_to(name)`
- [ ] `panels/component_list.py` — "Delete" button → `design.delete_component(name)` + refresh list
- [ ] `panels/options.py` — show component name + class in header when selected
  - `state.selected.observe(...)` → update header `HTML` widget

**You test (demo.ipynb cell 2):**
- Click a component on canvas → orange highlight appears, list highlights the row
- Click a row in the component list → canvas highlights that component
- "Zoom to" button → canvas zooms in
- "Delete" button → component disappears from list (but NOT from canvas until Rebuild)
- "Rebuild" → canvas redraws without deleted component

---

## Phase 3 — Options editor (Days 5–6)

**Goal:** Click a component → its options appear as an editable form.
Edit a value → click Rebuild → canvas updates.

**Tasks:**
- [ ] `utils.py` — `set_nested(dict, path, value)` helper
- [ ] `utils.py` — `options_to_widgets(opts, path, state, component)` recursive builder
  - Leaf → `HBox(Label(key), Text(value), Label(parsed))`
  - Nested dict → `Accordion` wrapping recursive call
  - `Text.observe` → `set_nested(component.options, path, val)` + `state.mark_dirty()`
- [ ] `utils.py` — `_try_parse(val, design)` — call `design.parse_value(str(val))`
- [ ] `panels/options.py`:
  - `state.selected.observe` → load component → call `options_to_widgets()`
  - Help tab: `HTML(inspect.getdoc(component.__class__))`
  - Source tab: `Textarea(inspect.getsource(component.__class__), disabled=True)`
  - Wrap all three in `ipywidgets.Tab`
- [ ] `toolbar.py` — "Rebuild" button:
  - **Wrap `design.rebuild()` in try/except** — verified: `design.rebuild()` RAISES
    `ValueError` (and others) when a component fails to build. Without try/except the
    entire GUI crashes. The log handler on `design.logger` will have already written the
    error there, so catch the exception and call `state.mark_clean()` only on success:
    ```python
    try:
        design.rebuild()
        canvas.render()
        comp_list.refresh()
        elements.refresh()
        state.mark_clean()
    except Exception:
        pass  # error already logged to design.logger → visible in Log panel
    ```
  - Do NOT call `state.mark_clean()` on failure — leave dirty flag set so user knows
    the rebuild did not succeed
- [ ] `toolbar.py` — `state.dirty.observe` → Rebuild button turns orange/warning colour when dirty

**You test (demo.ipynb cell 3):**
```python
# Select Q1, change pos_x in options form to "1mm", click Rebuild
# Q1 should move on canvas
```
- Edit `pos_x` → "Rebuild needed" indicator appears on button
- Click Rebuild → component moves on canvas
- Parsed value label next to `pos_x` shows `0.001` (metres)
- Help tab shows TransmonPocket docstring
- Source tab shows Python source

---

## Phase 4 — Library browser + Add component (Days 7–8)

**Goal:** Open library tab → find a component → fill in a name and options → click Create → component appears on canvas.

**Tasks:**
- [ ] `utils.py` — `discover_components()`:
  - `pkgutil.walk_packages` over `qiskit_metal.qlibrary`
  - Returns `dict[str, type]` of `{ClassName: Class}`
  - Cached at module load time
- [ ] `panels/library.py`:
  - Search `Text` box + `Select` widget populated by `discover_components()`
  - Filter: `Text.observe` → filter `Select.options` by substring match on class name
  - Click → show "Add component" `Accordion` below the list
  - Accordion contents:
    - Name `Text` input (default `ClassName_1`, auto-increments)
    - Options form: `options_to_widgets(dict(cls.default_options), [], state, None)`
      - Use `cls.default_options` (class attribute), NOT `cls.get_template_options()`
      - `get_template_options()` requires a live design in some subclasses and crashes
    - "Create" button
- [ ] Create button handler:
  - Dynamic import of selected class
  - `cls(design, name, options=Dict(**form_values))`
  - `design.rebuild()`
  - `canvas.render()`
  - Refresh component list
  - `state.select(name)` — auto-select newly created component

**You test (demo.ipynb cell 4):**
- Open Library tab
- Search "rectangle" → `Rectangle` appears
- Click it → options form appears with default values
- Change name to `"box1"`, click Create
- `box1` appears on canvas and in component list

---

## Phase 5 — Remaining panels + polish (Days 9–10)

**Tasks:**
- [ ] `panels/variables.py`:
  - Populate from `design.variables`
  - `HBox(Label(k), Text(v), Label(parsed))` per variable
  - "Add" button → two `Text` inputs + "Confirm"
  - "Delete" button per row
- [ ] `panels/elements.py`:
  - `Tab` with `Output` widgets for poly/path/junction
  - `refresh()` method: `display(design.qgeometry.tables['poly'])`
  - Filter by component name: `Text` → filter DataFrame
- [ ] `panels/netlist.py`:
  - `Output` + `display(design.net_info)` — the attribute is `net_info`, a DataFrame
  - Do NOT use `design.net_info_df` — that attribute does not exist
- [ ] `panels/log.py`:
  - `OutputWidgetHandler(out_widget)` logging handler
  - Attach to `design.logger` on GUI construction
  - "Clear" button → `out.clear_output()`
- [ ] `toolbar.py` — remaining buttons:
  - "Save design" → text input for filename → `design.to_python_script(filename)`
  - "Delete all" → confirmation toggle → `design.delete_all_components()` + refresh
  - "Screenshot" → `fig.savefig(buf, format='png')` + `display(Image(data=buf.getvalue()))`
  - "Zoom to fit" → `ax.autoscale()` + `draw_idle()`
  - "Toggle panels" → `left_tabs.layout.display = 'none'/'flex'`
  - "Export GDS" → text input + `design.renderers.gds.export_to_gds(path)`
- [ ] `canvas.py` — hover label: `mpl_connect('motion_notify_event')` → update a status label below the canvas with nearest component name

**You test (demo.ipynb cell 5):**
- Variables: add `qubit_size = 450um`, verify it appears in parsed values
- Elements tab: select Q1 in component list, verify poly table filters to Q1 rows
- Log: trigger a warning → appears in Log tab
- Screenshot: button → inline PNG appears below the button
- Save: button → `.metal.py` file written

---

## Phase 6 — Integration + packaging (Day 11)

**Tasks:**
- [ ] Move `_dev/jupyter_gui/demo.ipynb` to `tutorials/quick-topics/Jupyter-GUI-demo.ipynb`
- [ ] Add `docs/tut/quick-topics/Jupyter-GUI-demo.ipynb` (docs copy)
- [ ] Update `src/qiskit_metal/__init__.py` to export `gui`
- [ ] Update `pyproject.toml` if any new dep added (none expected)
- [ ] Add to `tests/` — `test_jupyter_gui.py`:
  - Top of file: `ipywidgets = pytest.importorskip('ipywidgets')` — skips entire module
    on `quantum-metal` (no `[notebook]`) installs and in the `tests-lite` CI job
  - **Backend note for CI:** `CanvasPanel.__init__` calls `plt.subplots()`. In CI the
    backend is `Agg`, not `ipympl`. `fig.canvas.toolbar_visible` and `draw_idle()` both
    work on Agg (verified). `self.widget` will be `FigureCanvasAgg`, not an ipympl widget.
    This is acceptable for unit tests — the test environment never calls `display(gui)`.
    Tests must NOT assert `isinstance(canvas.widget, ipympl...)`.
  - **Confirmed safe method names:** `design.delete_component(name: str)` ✓,
    `design.delete_all_components()` ✓, `design.net_info` (DataFrame property) ✓
  - `test_gui_returns_widget` — `isinstance(qm.gui(design), ipywidgets.Widget)` ← tests the
    root VBox, not canvas.widget — this is correct
  - `test_gui_no_qt_import` — build GUI, assert `'PySide6'` not in `sys.modules`
  - `test_canvas_renders` — `canvas.render()` doesn't raise (works with Agg in CI)
  - `test_options_form_writes_back` — edit an option, verify `component.options` updated
  - `test_rebuild_error_no_crash` — set bad options on a component, call rebuild button
    handler, assert GUI widget is still accessible (no exception propagated)
  - `test_create_component_via_library` — programmatic "Create" → component in `design.components`
  - `test_gui_close_removes_log_handler` — call `gui.close()`, verify handler count on
    `design.logger` returns to baseline (catches the duplicate-handler re-run bug)
- [ ] Update `CLAUDE.md` — add `src/qiskit_metal/jupyter_gui/` to architecture map
- [ ] Update `docs/headless-usage.rst` — add `qm.gui()` section

---

## Scope boundaries (for the AI agent)

**In scope:**
- Everything in Phases 0–5 above
- Zero new hard dependencies
- All panels described in `feature-map.md` marked ✅

**Out of scope (do not implement):**
- Drag-to-place components on canvas
- anywidget / WebGL canvas
- ipytree library browser (flat Select only)
- HFSS / Q3D launcher (stub text only)
- Editable QGeometry table
- Row-level inline rename in component list
- Right-click context menus

**Performance contract:**
- `canvas.render()` must not block for more than 2 seconds for a design
  with ≤50 components (same as `qm.view()` today)
- Options form rebuild must take <200ms for options dicts with ≤100 keys
- No 500ms polling timers — refresh only on user action
