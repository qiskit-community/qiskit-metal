.. _overview:

*********************
Qiskit Metal Overview
*********************

.. image:: images/overview.jpg
   :alt: Missing Overview Diagram

**Analyses**

.. list-table:: Analyses grouping
   :widths: 10 90
   :header-rows: 1

   * - Group
     - Description
   * - Hamiltonian
     - Module containing all Qiskit Metal hamiltonian-only analyses.
   * - Sweep_Options
     - Module containing all Qiskit Metal sweeping options for analyses.

.. list-table:: Analyses details
   :widths: 10 90
   :header-rows: 1

   * - Class
     - Description
   * - Hcpb
     - Used to model analytically the CPB Hamiltonian quickly and efficiently. Solves tridiagonal eigenvalue problem for arbitrary Ej, Ec, ng values.
   * - Sweeping
     - Need access to renderers which are registered in QDesign.

**QLibrary**

.. list-table:: Components details
   :widths: 10 90
   :header-rows: 1

   * - Class
     - Description
   * - BaseQubit
     - Qubit base class. Use to subscript, not to generate directly.  Has connection lines that can be added.
   * - CapThreeFinger
     - Create a three finger planar capacitor with a ground pocket cuttout. The width of the fingers is determined by the trace width.
   * - CircleCaterpillar
     - A single configurable circle.
   * - CircleRaster
     - A single configurable circle.
   * - LaunchpadWireband
     - Launch pad to feed/read signals to/from the chip.
   * - LauchpadWirebandCoupled
     - Launch pad to feed/read signals to/from the chip.
   * - NGon
     - A n-gon polygon.
   * - NSquareSpiral
     - A n count square spiral.
   * - ParsedDynamicAttributes_Component
     - Provides a parsing view of the component options
   * - QComponent
     - QComponent is the base class for all Metal components and is the central construct from which all components in Metal are derived.
   * - QRouteLead
     - A simple class to define a an array of points with some properties, defines 2D positions and some of the 2D directions (XY plane). All values stored as np.ndarray of parsed floats.  QRouteLead is a simple sequence of points.  Used to accurately control one of the QRoute termination points.
   * - QRoutePoint
     - A convenience wrapper class to define an point with orientation, with a 2D position and a 2D direction (XY plane). All values stored as np.ndarray of parsed floats.
   * - QRoute
     - Super-class implementing routing methods that are valid irrespective of the number of pins (>=1). The route is stored in a n array of planar points (x,y coordinates) and one direction, which is that of the last point in the array Values are stored as np.ndarray of parsed floats or np.array float pair.
   * - Rectangle
     - A single configurable square.
   * - RectangleHollow
     - A single configurable square.
   * - RestonatorRectangleSpiral
     - A rectnagle spiral resonator based on length input. The X dimension is modified by the code based on the total length inputed.
   * - RouteAnchors
     - Creates and connects a series of anchors through which the Route passes.
   * - RouteFramed
     - A non-meandered basic CPW that is auto-generated between 2 components. Designed to avoid self-collisions and collisions with components it is attached to.
   * - RouteMeander
     - The base CPW meandered class.  Implements a simple CPW, with a single meander
   * - RouteMixed
     - The comprehensive Routing class Inherits RoutePathfinder, RouteMeander class, thus also QRoute and RouteAnchors.  Implements fully featured Routing, allowing different type of connections between anchors.
   * - RoutePathfinder
     - Non-meandered CPW class that combines A* pathfinding algorithm with simple 1-, 2-, or S-shaped segment checks and user-specified anchor points. 1. A* heap modified to prioritize paths with shortest length_travelled + Manhattan distance to destination. 2. Checks if connect_simple is valid each time we pop from the heap. If so, use it, otherwise proceed with A*. 3. Tweaks connect_simple to account for end anchor direction in determining which CPW (elbow or S-segment) to use.
   * - RouteStraight
     - Draw a straight Route connecting two pins.
   * - TransmonConcentric
     - The base TrasmonConcentric class.  Metal transmon object consisting of a circle surrounding by a concentric ring. There are two Josephson Junction connecting the circle to the ring; one at the south end and one at the north end. There is a readout resonator.
   * - TransmonCross
     - The base TransmonCross class.  Simple Metal Transmon Cross object. Creates the A cross-shaped island, the “junction” on the south end, and up to 3 connectors on the remaining arms (claw or gap).
   * - TransmonPocket
     - The base TransmonPocket class.  Create a standard pocket transmon qubit for a ground plane, with two pads connected by a junction (see drawing below).  Connector lines can be added using the connection_pads dictionary. Each connector pad has a name and a list of default properties.
   * - TransmonPocketCL
     - The base TransmonPocketCL class.  Create a standard pocket transmon qubit for a ground plane, with two pads connected by a junction (see drawing below).  Connector lines can be added using the connection_pads dictionary. Each connector line has a name and a list of default properties.

**Designs**

.. list-table:: Designs details
   :widths: 10 90
   :header-rows: 1

   * - Class
     - Description
   * - Components
     - This is a user interface for the design._components dict. The keys are unique integers, however, this interface allows user to treat the keys as strings.  Set up variables and logger which are used to emulate a dict which is referencing design._components.
   * - DesignPlanar
     - Metal class for a planar (2D) design, consisting of a single plane chip. Typically assumed to have some CPW geometires.
   * - QDesign
     - QDesign is the base class for Qiskit Metal Designs. A design is the most top-level object in all of Qiskit Metal.  Create a new Metal QDesign.
   * - QNet
     - Use DataFrame to hold Net Information about the connected pins of a design. There is one uniqe net_id for each connected pin.  Hold the net information of all the USED pins within a design.

**QGeometryTables**

.. list-table:: QGeometryTables details
   :widths: 10 90
   :header-rows: 1

   * - Class
     - Description
   * - QGeometryTables
     - Class to create, store, and handle element tables.

**GUI**

.. list-table:: GUI details
   :widths: 10 90
   :header-rows: 1

   * - Class
     - Description
   * - MetalGui
     - Qiskit Metal Main GUI.  This class extends the QMainWindowBaseHandler class.  The GUI can be controled by the user using the mouse and keyboard or API for full control.

**Renderers**

.. list-table:: Renderers details
   :widths: 10 90
   :header-rows: 1

   * - Class
     - Description
   * - AnimatedText
     - Class that animates text.
   * - Cheesing
     - Create a cheese cell based on input of no-cheese locations.
   * - MplInteraction
     - Base class for class providing interaction to a matplotlib Figure.
   * - PanAndZoom
     - Class providing pan & zoom interaction to a matplotlib Figure. Left button for pan, right button for zoom area and zoom on wheel. Support subplots, twin Axes and log scales.
   * - PlotCanvas
     - Main Plot canvas widget.
   * - QGDSRenderer
     - Extends QRenderer to export GDS formatted files. The methods which a user will need for GDS export should be found within this class.  All chips within design should be exported to one gds file. For the “subtraction box”: 1. If user wants to export the entire design, AND if the base class of QDesign._chips[chip_name][‘size’] has dict following below example: {‘center_x’: 0.0, ‘center_y’: 0.0, ‘size_x’: 9, ‘size_y’: 6} then this box will be used for every layer within a chip.  2. If user wants to export entire design, BUT there is not information in QDesign._chips[chip_name][‘size’], then the renderer will calcuate the size of all of the components and use that size for the “subtraction box” for every layer within a chip.  3. If user wants to export a list of explicit components, the bounding box will be calculated by size of QComponents in the QGeometry table. Then be scaled by bounding_box_scale_x and bounding_box_scale_y.  4. Note: When using the Junction table, the cell for Junction should be “x-axis” aligned and then GDS rotates based on LineString given in Juction table.
   * - QMplRenderer
     - Matplotlib handle all rendering of an axis.  The axis is given in the function render.
   * - QRenderer
     - Abstract base class for all Renderers of Metal designs and their components and qgeometry.
   * - QRendererGui
     - Abstract base class for the GUI rendering. Extends QRenderer. An interface class.
   * - ZoomOnWheel
     - Class providing zoom on wheel interaction to a matplotlib Figure.  This class extends the MplInteraction class.  Supports subplots, twin Axes and log scales.

**Toolbox_Metal**

.. list-table:: Toolbox_Metal details
   :widths: 10 90
   :header-rows: 1

   * - Class
     - Description
   * - QiskitMetalDesignError
     - Custom Exception to indicate User action is needed to correct Design Inputs.
   * - QiskitMetalExceptions
     - Custom Exception super-class. Every Exception raised by qiskit-metal should inherit this. Adds the qiskit-metal prefix.
   * - IncorrectQtException
     - Run PySide2 only
