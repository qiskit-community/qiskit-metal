// -----------------------------------------------------------------------------
//
//  Gmsh C++ extended tutorial 3
//
//  Post-processing data import: list-based
//
// -----------------------------------------------------------------------------

#include <set>
#include <iostream>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  // Gmsh supports two types of post-processing data: "list-based" and
  // "model-based". Both types of data are handled through the `view' interface.

  // List-based views are completely independent from any model and any mesh:
  // they are self-contained and simply contain lists of coordinates and values,
  // element by element, for 3 types of fields (scalar "S", vector "V" and
  // tensor "T") and several types of element shapes (point "P", line "L",
  // triangle "T", quadrangle "Q", tetrahedron "S", hexahedron "H", prism "I"
  // and pyramid "Y"). (See `x4.cpp' for a tutorial on model-based views.)

  // To create a list-based view one should first create a view:
  int t1 = gmsh::view::add("A list-based view");

  // List-based data is then added by specifying the type as a 2 character
  // string that combines a field type and an element shape (e.g. "ST" for a
  // scalar field on triangles), the number of elements to be added, and the
  // concatenated list of coordinates (e.g. 3 "x" coordinates, 3 "y"
  // coordinates, 3 "z" coordinates for first order triangles) and values for
  // each element (e.g. 3 values for first order scalar triangles, repeated for
  // each step if there are several time steps).

  // Let's create two triangles...
  std::vector<double> triangle1 = {
    0., 1., 1., // x coordinates of the 3 triangle nodes
    0., 0., 1., // y coordinates of the 3 triangle nodes
    0., 0., 0.}; // z coordinates of the 3 triangle nodes
  std::vector<double> triangle2 = {0., 1., 0., 0., 1., 1., 0., 0., 0.};

  // ... and append values for 10 time steps
  for(int step = 0; step < 10; step++) {
    // 3 node values for each step
    triangle1.insert(triangle1.end(), {10., 11. - step, 12.});
    triangle2.insert(triangle2.end(), {11., 12., 13. + step});
  }

  // List-based data is just added by concatenating the data for all the
  // triangles:
  std::vector<double> triangles(triangle1);
  triangles.insert(triangles.end(), triangle2.begin(), triangle2.end());
  gmsh::view::addListData(t1, "ST", 2, triangles);

  // Internally, post-processing views parsed by the .geo file parser create
  // such list-based data (see e.g. `t7.cpp', `t8.cpp' and `t9.cpp'),
  // independently of any mesh.

  // Vector or tensor fields can be imported in the same way, the only
  // difference beeing the type (starting with "V" for vector fields and "T" for
  // tensor fields) and the number of components. For example a vector field on
  // a line element can be added as follows:
  std::vector<double> line = {0.,  1., // x coordinate of the 2 line nodes
                              1.2, 1.2, // y coordinate of the 2 line nodes
                              0.,  0.}; // z coordinate of the 2 line nodes

  for(int step = 0; step < 10; step++) {
    // 3 vector components for each node (2 nodes here), for each step
    line.insert(line.end(), {10. + step, 0., 0., 10. + step, 0., 0.});
  }
  gmsh::view::addListData(t1, "VL", 1, line);

  // List-based data can also hold 2D (in window coordinates) and 3D (in model
  // coordinates) strings (see `t4.cpp'). Here we add a 2D string located on the
  // bottom-left of the window (with a 20 pixels offset), as well as a 3D string
  // located at model coordinates (0.5, 0.5. 0):
  gmsh::view::addListDataString(t1, {20., -20.}, {"Created with Gmsh"});
  gmsh::view::addListDataString(t1, {0.5, 1.5, 0.},
                                {"A multi-step list-based view"},
                                {"Align", "Center", "Font", "Helvetica"});

  // The various attributes of the view can be queried and changed using the
  // option interface:
  gmsh::view::option::setNumber(t1, "TimeStep", 5);
  gmsh::view::option::setNumber(t1, "IntervalsType", 3);
  double ns;
  gmsh::view::option::getNumber(t1, "NbTimeStep", ns);
  std::cout << "View " << t1 << " has " << ns << " time steps" << std::endl;

  // Views can be queried and modified in various ways using plugins (see
  // `t9.py'), or probed directly using `gmsh::view::probe()' - here at point
  // (0.9, 0.1, 0):
  std::vector<double> val;
  double distance;
  gmsh::view::probe(t1, 0.9, 0.1, 0, val, distance);
  std::cout << "Value at (0.9, 0.1, 0):";
  for(auto v : val) std::cout << " " << v;
  std::cout << std::endl;

  // Views can be saved to disk using `gmsh::view::write()':
  gmsh::view::write(t1, "x3.pos");

  // High-order datasets can be provided by setting the interpolation matrices
  // explicitly. Let's create a second view with second order interpolation on a
  // 4-node quadrangle.

  // Add a new view:
  int t2 = gmsh::view::add("Second order quad");

  // Set the node coordinates:
  std::vector<double> quad = {
    0.,   1.,   1.,   0., // x coordinates of the 4 quadrangle nodes
    -1.2, -1.2, -0.2, -0.2, // y coordinates of the 4 quadrangle nodes
    0.,   0.,   0.,   0.}; // z coordinates of the 4 quadrangle nodes

  // Add nine values that will be interpolated by second order basis functions
  quad.insert(quad.end(), {1., 1., 1., 1., 3., 3., 3., 3., -3.});

  // Set the two interpolation matrices c[i][j] and e[i][j] defining the d = 9
  // basis functions: f[i](u, v, w) = sum_(j = 0, ..., d - 1) c[i][j] u^e[j][0]
  // v^e[j][1] w^e[j][2], i = 0, ..., d-1, with u, v, w the coordinates in the
  // reference element:
  gmsh::view::setInterpolationMatrices(
    t2, "Quadrangle", 9,
    {0,    0,   0.25,  0,    0,   -0.25, -0.25, 0,    0.25, 0,     0,   0.25,
     0,    0,   -0.25, 0.25, 0,   -0.25, 0,     0,    0.25, 0,     0,   0.25,
     0.25, 0,   0.25,  0,    0,   0.25,  0,     0,    0.25, -0.25, 0,   -0.25,
     0,    0,   -0.5,  0.5,  0,   0.5,   0,     -0.5, 0,    0,     0.5, -0.5,
     0,    0.5, 0,     -0.5, 0,   0,     0,     0,    -0.5, 0.5,   0,   -0.5,
     0,    0.5, 0,     0,    0.5, -0.5,  0,     -0.5, 0,    0.5,   0,   0,
     1,    -1,  1,     -1,   0,   0,     0,     0,    0},
    {0, 0, 0, 2, 0, 0, 2, 2, 0, 0, 2, 0, 1, 0,
     0, 2, 1, 0, 1, 2, 0, 0, 1, 0, 1, 1, 0});

  // Note that two additional interpolation matrices could also be provided to
  // interpolate the geometry, i.e. to interpolate curved elements.

  // Add the data to the view:
  gmsh::view::addListData(t2, "SQ", 1, quad);

  // In order to visualize the high-order field, one must activate adaptive
  // visualization, set a visualization error threshold and a maximum
  // subdivision level (Gmsh does automatic mesh refinement to visualize the
  // high-order field with the requested accuracy):
  gmsh::view::option::setNumber(t2, "AdaptVisualizationGrid", 1);
  gmsh::view::option::setNumber(t2, "TargetError", 1e-2);
  gmsh::view::option::setNumber(t2, "MaxRecursionLevel", 5);

  // Launch the GUI to see the results:
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
