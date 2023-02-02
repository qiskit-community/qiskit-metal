This directory contains the Gmsh tutorials.

The `.geo' files are written in Gmsh's built-in scripting language. You can open
them directly with the Gmsh app: in the graphical user interface (GUI), just go
to `File->Open', select e.g. the first tutorial (`t1.geo') and choose "Open"; on
the command line, run "gmsh t1.geo" (which will launch the GUI) or "gmsh t1.geo
-2" (to perform 2D meshing in batch mode).

 * Binary versions of the Gmsh app for Windows, Linux and macOS can be
   downloaded from https://gmsh.info. Several Linux distributions also ship the
   Gmsh app. See the top-level `README.txt' file in the Gmsh source code for
   instructions on how to compile the app from source.

The `c++', `c', `python' and `julia' subdirectories contain the C++, C, Python
and Julia tutorials, written using the Gmsh Application Programming Interface
(API). You will need the Gmsh dynamic library and the associated header files
(for C++ and C) or modules (for Python and Julia) to run them. Each subdirectory
contains additional information on how to run the tutorials for each supported
language, as well as extended tutorials (starting with `x') introducing features
available through the API but not available in `.geo' files.

 * A binary Software Development Kit (SDK) for Windows, Linux and macOS, that
   contains the dynamic Gmsh library and the associated header and module files,
   can be downloaded from https://gmsh.info. Python users can use `pip install
   --upgrade gmsh', which will download the binary SDK automatically, and
   install the files in the appropriate system directories. Several Linux
   distributions also ship the Gmsh SDK. See the top-level `README.txt' in the
   Gmsh source code for instructions on how to compile the dynamic Gmsh library
   from source.

Table of contents
=================

* t1: Geometry basics, elementary entities, physical groups
* t2: Transformations, extruded geometries, volumes
* t3: Extruded meshes, parameters, options
* t4: Built-in functions, holes in surfaces, annotations, entity colors
* t5: Mesh sizes, loops, holes in volumes
* t6: Transfinite meshes
* t7: Background meshes
* t8: Post-processing and animations
* t9: Plugins
* t10: Mesh size fields
* t11: Unstructured quadrangular meshes
* t12: Cross-patch meshing with compounds
* t13: Remeshing an STL file without an underlying CAD model
* t14: Homology and cohomology computation
* t15: Embedded points, lines and surfaces
* t16: Constructive Solid Geometry, OpenCASCADE geometry kernel
* t17: Anisotropic background mesh
* t18: Periodic meshes
* t19: Thrusections, fillets, pipes, mesh size from curvature
* t20: STEP import and manipulation, geometry partitioning
* t21: Mesh partitioning

Extended tutorials (API only):

* x1: Geometry and mesh data
* x2: Mesh import, discrete entities, hybrid models, terrain meshing
* x3: Post-processing data import: list-based
* x4: Post-processing data import: model-based
* x5: Additional geometrical data: parametrizations, normals, curvatures
* x6: Additional mesh data: integration points, Jacobians and basis functions
* x7: Additional mesh data: internal edges and faces
