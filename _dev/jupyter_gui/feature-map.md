# Feature Map: MetalGUI → Jupyter GUI

For each MetalGUI panel: what it does, how it reads/writes the design,
and what the Jupyter equivalent is.

Source of truth for the audit: `src/qiskit_metal/_gui/`.

---

## 1. Chip Canvas

**MetalGUI class:** `PlotCanvas` + `QMplRenderer` + `PanAndZoom`
**File:** `renderers/renderer_mpl/mpl_canvas.py`

| Feature | MetalGUI | Jupyter | Status |
|---------|----------|---------|--------|
| Render chip geometry | `QMplRenderer.render(ax)` | Same call — already works in `qm.view()` | ✅ Full port |
| Pan | Left-click drag (`PanAndZoom`) | ipympl toolbar built-in | ✅ |
| Zoom scroll | Mouse wheel (`PanAndZoom`) | ipympl toolbar built-in | ✅ |
| Zoom to fit | `ax.autoscale()` | Button → same call | ✅ |
| Zoom to component | `canvas.zoom_to_components(names)` → `ax.set_xlim/ylim` | Button + `ax.set_xlim/ylim(component_bounds)` | ✅ |
| Click to select component | Qt mouse event → bounding box hit test | `mpl_connect('button_press_event')` → nearest centroid | ✅ |
| Highlight selected component | `canvas.highlight_components()` → coloured patch | Same matplotlib patch approach | ✅ |
| Right-click region zoom | Qt right-drag | ❌ Not available in ipympl | Skip |
| Component label on hover | Qt hover tooltip | `mpl_connect('motion_notify_event')` → update label widget | ✅ Partial |
| Watermark / logo | `_axis_set_watermark_img()` | Same call or omit | Optional |

**Design reads:**
- `design.qgeometry.tables` — all geometry
- `component.qgeometry_bounds()` — for zoom/highlight

**Key implementation note:** The canvas must call `fig.canvas.draw_idle()` after
every render update, not `fig.canvas.draw()`, to avoid blocking the event loop.

---

## 2. Component List

**MetalGUI class:** `QTableModel_AllComponents` in `dockDesign`
**File:** `_gui/widgets/all_components/table_model_all_components.py`

**What it reads from design:** `design.components` dict — keys are names,
values are component instances. Columns shown: name, class name, module path.

**Auto-refresh:** 500ms timer detects row count change → resets model.

| Feature | MetalGUI | Jupyter | Status |
|---------|----------|---------|--------|
| List all components | `design.components` table | `ipywidgets.Select` populated from `design.components` | ✅ |
| Filter by name/class | QSortFilterProxyModel + text box | Python-side string filter on `Select` options | ✅ |
| Click → load options | Selection → `gui.edit_component(name)` | `.observe('value')` → update options panel | ✅ |
| Click → highlight on canvas | Selection → `canvas.highlight_components()` | Same, triggered by observe | ✅ |
| Zoom to component | Button per row | "Zoom to selected" button below list | ✅ |
| Delete component | Button per row | "Delete selected" button → `design.delete_component(name)` | ✅ |
| Rename component | Double-click cell edit | Not in Tier 1 | ❌ Skip |
| Auto-refresh | 500ms Qt timer | Manual "Refresh" button + refresh after every action | ✅ Partial |
| Show class / module columns | Table columns | Collapsible detail below list | ✅ Simplified |

---

## 3. Options Editor

**MetalGUI class:** `ComponentWidget` (3 tabs) + `QTreeModel_Options`
**File:** `_gui/widgets/edit_component/component_widget.py`

**What it reads:** `component.options` — a nested `addict.Dict`.
**What it writes:** Direct mutation of `component.options[key] = value`.
**Parsed value:** `design.parse_value(str)` — evaluates `"10mm"` → `10` (stays in mm, Metal's
internal unit is mm). Do NOT display the parsed value as metres — it is NOT `0.001`.

| Feature | MetalGUI | Jupyter | Status |
|---------|----------|---------|--------|
| Options form (nested) | Qt tree, 3 cols: name/value/parsed | Recursive `ipywidgets.Accordion` + `Text` fields | ✅ |
| Live parsed value preview | 3rd column in tree | Grey label next to each field updated on change | ✅ |
| Edit option → write to component | `QTreeModel.setData()` → `component.options[path] = val` | `Text.observe('value')` → same mutation | ✅ |
| Rebuild button | Separate toolbar button | Button in options panel header | ✅ |
| Help tab (docstring) | `QTextBrowser` with HTML | `ipywidgets.HTML(inspect.getdoc(...))` | ✅ |
| Source tab | QTextEdit with Python source | `ipywidgets.Textarea(inspect.getsource(...))` | ✅ |
| Placeholder when nothing selected | Qt placeholder text | `ipywidgets.Label("Select a component...")` | ✅ |
| Nested dict → collapsible sections | Qt tree expand/collapse | `ipywidgets.Accordion` | ✅ |
| Boolean option | Qt checkbox | `ipywidgets.Checkbox` | ✅ |
| Syntax-highlighted source | Qt syntax delegate | `pygments` HTML (already a Jupyter dep) | ✅ |

**Key implementation note:** Options are nested arbitrarily deep.
The rendering function must be recursive:
```python
def options_to_widgets(opts: dict, path: list, component) -> VBox:
    rows = []
    for key, val in opts.items():
        if isinstance(val, dict):
            rows.append(Accordion([options_to_widgets(val, path+[key], component)],
                                   titles=[key]))
        else:
            w = Text(value=str(val))
            w.observe(lambda change, p=path+[key]:
                set_nested(component.options, p, change['new']), names='value')
            rows.append(HBox([Label(key), w, Label(parsed(val))]))
    return VBox(rows)
```

---

## 4. Design Variables

**MetalGUI class:** `PropValTable` in `dockVariables`
**File:** `_gui/widgets/variable_table/prop_val_table_gui.py`

**What it reads/writes:** `design.variables` dict.
**Parsed value:** `design.parse_value(val)` — e.g. `"10 mm"` → `0.01` (metres).

| Feature | MetalGUI | Jupyter | Status |
|---------|----------|---------|--------|
| Show all variables | Table rows | `VBox` of `HBox(Label, Text, Label_parsed)` | ✅ |
| Edit value | In-place table edit | `Text` widget with `observe` | ✅ |
| Add variable | "+" button + new row | "Add" button + two `Text` inputs (name + value) | ✅ |
| Delete variable | Delete button per row | "Delete selected" button | ✅ |
| Live parsed value | 3rd column | Grey label updated on change | ✅ |

---

## 5. Component Library Browser

**MetalGUI class:** `TreeViewQLibrary` + `QFileSystemLibraryModel`
**File:** `_gui/widgets/qlibrary_display/`

**What it reads:** File system scan of `qiskit_metal/qlibrary/` directory.
Icons from `_imgs/components/*.png`. Docstring metadata for display name.

| Feature | MetalGUI | Jupyter | Status |
|---------|----------|---------|--------|
| Show all components | File tree with folder grouping | Flat `Select` list, grouped by prefix | ✅ Simplified |
| Search/filter | Text box → QSortFilterProxyModel | Text box → Python filter on list | ✅ |
| Component icons | PNG thumbnails | ❌ Text only in Tier 1 | Skip |
| Click → add component form | Opens `ParameterEntryWindow` | Inline `Accordion` with options form | ✅ |
| Add component form: name field | Text input | `Text` widget | ✅ |
| Add component form: options | Nested tree | Same recursive widget as options editor | ✅ |
| "Create" button | `instantiate_qcomponent()` → `design.add_component()` | Button → dynamic import + `ComponentClass(design, name, options=...)` | ✅ |
| Default options shown | `ComponentClass.get_template_options()` | Same call | ✅ |

**Discovery mechanism (no file system needed):**
```python
import pkgutil, importlib, inspect
import qiskit_metal.qlibrary as lib
from qiskit_metal.qlibrary.core import QComponent

components = {}
for importer, modname, ispkg in pkgutil.walk_packages(
        lib.__path__, prefix=lib.__name__ + '.'):
    try:
        mod = importlib.import_module(modname)
    except Exception:
        continue
    for name, cls in inspect.getmembers(mod, inspect.isclass):
        if issubclass(cls, QComponent) and cls is not QComponent:
            components[name] = cls
```
This avoids the file system entirely and works on all platforms. Verified: finds ~45 components.
The `try/except` around `import_module` is required — some submodules depend on optional
heavy packages (e.g. ansys, gmsh) and will ImportError on a lite install.

**Default options:** Use `cls.default_options` (a class attribute) to read template options
**without instantiating the class**. Do NOT call `cls.get_template_options(design=None)` —
that method signature requires a live design in some subclasses and will raise `AttributeError`.

---

## 6. Elements / QGeometry Table

**MetalGUI class:** `ElementTableModel` in `tabQGeometry`
**File:** `_gui/elements_window.py`

**What it reads:** `design.qgeometry.tables` — dict of pandas DataFrames
keyed by element type (`"poly"`, `"path"`, `"junction"`).

| Feature | MetalGUI | Jupyter | Status |
|---------|----------|---------|--------|
| Show tables by type | Tabs (poly/path/junction) | `ipywidgets.Tab` + `Output` + `display(df)` | ✅ |
| Filter by component name | Text box → filter column | Python: `df[df['component']==name]` | ✅ |
| Filter by layer | Text box → filter column | Python: `df[df['layer']==n]` | ✅ |
| Editable cells | Qt table edit | ❌ Read-only in Tier 1 | Skip |
| Auto-refresh | 500ms timer | Refresh after rebuild action | ✅ Partial |

---

## 7. Net List / Connectors

**MetalGUI class:** `NetListTableModel` in `dockConnectors` / `tabNetList`

**What it reads:** `design.net_info` (a DataFrame already — no `.net_info_df` attribute exists)
and `design.components[n].pins` for pin-to-pin connections.

| Feature | MetalGUI | Jupyter | Status |
|---------|----------|---------|--------|
| Show all connections | Table | `Output` + `display(design.net_info)` | ✅ |
| Filter by text | Text box | Python string filter | ✅ |

---

## 8. Log Panel

**MetalGUI class:** `QTextEditLogger` in `dockLog`

| Feature | MetalGUI | Jupyter | Status |
|---------|----------|---------|--------|
| Capture Python logger | Qt logging handler | `logging.Handler` subclass that writes to `Output` widget | ✅ |
| Scroll log | Qt scroll | `Output` widget scrolls natively | ✅ |
| Clear log | Not in MetalGUI | "Clear" button → `output.clear_output()` | ✅ Better |

```python
class OutputWidgetHandler(logging.Handler):
    def __init__(self, output_widget):
        super().__init__()
        self.out = output_widget
    def emit(self, record):
        with self.out:
            print(self.format(record))
```

**Critical lifecycle note:** When the GUI is closed or the cell is re-run, the handler must
be removed from the logger. Otherwise the next `gui()` call registers a second handler and
every log message appears twice — and continues writing to the now-dead `Output` widget.

```python
# In gui.py or LogPanel.close():
design.logger.removeHandler(handler)
```

The `gui()` function must return an object with a `close()` method (or use `__del__`) that
calls `removeHandler`. The root `W.VBox` can be subclassed for this:

```python
class MetalGui(W.VBox):
    def close(self):
        self._log_panel.detach()  # calls design.logger.removeHandler(...)
        super().close()
```

---

## 9. Toolbar Actions

| MetalGUI button | Design call | Jupyter | Status |
|-----------------|-------------|---------|--------|
| Rebuild | `design.rebuild()` + refresh canvas | Button with try/except — `design.rebuild()` RAISES on component error | ✅ |
| Refresh (no rebuild) | redraw canvas | Button | ✅ |
| Save design | `design.to_python_script(path)` | Button + filename `Text` | ✅ |
| Delete all | `design.delete_all_components()` | Button + confirm toggle | ✅ |
| Screenshot | `fig.savefig(buf)` + `display(Image)` | Button | ✅ |
| Zoom to fit | `ax.autoscale()` + `fig.canvas.draw_idle()` | Button | ✅ |
| Toggle panels | Show/hide left/right panels | Button → `layout.display='none'/'flex'` | ✅ |
| Open docs | webbrowser / URL | HTML link | ✅ |
| GDS export | `design.renderers.gds.export_to_gds(path)` | Button + filename `Text` | ✅ |
| HFSS launch | Windows COM only | Stub button → HTML message | ⚠️ Stub |
| Theme switch | Qt stylesheet | ipympl figure style + widget CSS | Partial |

---

## What does NOT port (Tier 1)

| Feature | Reason | Future path |
|---------|--------|-------------|
| Drag-to-place on canvas | Needs native events + hit testing | anywidget Tier 2 |
| Right-click menus | ipympl no right-click support | Context panel as alternative |
| Component icons in library | PNG assets, complex to embed | Optional `ipytree` Tier 2 |
| Row-level delete/rename in table | Complex inline edit UX | Tier 2 |
| HFSS / Q3D launcher | Windows-only COM | Stub with instructions |
| Build history (detailed) | Complex scroll UI | Simple log output |
| Editable QGeometry table | Risky — modify geometry directly | Out of scope |
