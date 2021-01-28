# Qiskit Metal Architecture
The high level Metal architecture is diagramed in the overview below.  The user workflow is diagramed in the workflow link below as well.

* [Overview](/docs/overview.rst)
* [Workflow](/docs/workflow.rst)

## Required Attributes

### QLibrary Components
A base qlibrary component contains several attributes and a method that must be overridden by qlibrary components that extend the base.

**Attributes**
| Attribute          | Description                                            |
| ------------------ | ------------------------------------------------------ |
| default_options    | Default drawing options                                |
| component_metadata | Component metadata                                     |
| options            | A dictionary of the component-desinger-defined options |

**Methods**
| Method | Description |
| ------ | ----------- |
| make   | The make function implements the logic that creates the geometry (poly, path, etc.) from the qcomponent.options dictionary of parameters, and the adds them to the design, using qcomponent.add_qgeometry(...), adding in extra needed information, such as layer, subtract, etc. |

### QRenderer
A base qrenderer contains several attributes and several methods that must be overridden by qrenderers that extend the base.

**Attributes**
| Attribute          | Description                   |
| ------------------ | ----------------------------- |
| name               | Renderer name                 |
| element_extensions | Element extentions dictionary |
| element_table_data | Element table data            |

**Methods**
| Method              | Description                                                                             |
| ------------------- | --------------------------------------------------------------------------------------- |
| render_chips        | Render all chips of the design.  Calls render_chip for each chip.                       |
| render_chip         | Render the given chip.                                                                  |
| render_components   | Render all components of the design.  If selection is none, then render all components. |
| render_component    | Render the specified component.                                                         |
| render_element      | Render the specified element.                                                           |
| render_element_path | Render an element path.                                                                 |
| render_element_poly | Render an element poly.                                                                 |

### QRendererGui
In addition to the attributes and methods that must be overwritten by any QRenderer, a base qrenderergui has additional methods that must be overwritten by all qrendererguis that extend the base.

| Method            | Description                 |
| ----------------- | --------------------------- |
| setup_fig         | Setup the given figure.     |
| style_axis        | Style the axis.             |
| render_design     | Render the design.          |
| render_component  | Render the given component. |
| render_shapely    | Render shapely.             |
| render_connectors | Render connectors.          |
| clear_axis        | Clear the axis.             |
| clear_figure      | Clear the figure.           |
