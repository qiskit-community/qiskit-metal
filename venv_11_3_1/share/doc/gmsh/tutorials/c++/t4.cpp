// -----------------------------------------------------------------------------
//
//  Gmsh C++ tutorial 4
//
//  Holes in surfaces, annotations, entity colors
//
// -----------------------------------------------------------------------------

#include <set>
#include <cmath>
#include <gmsh.h>

double hypoth(double a, double b) { return sqrt(a * a + b * b); }

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  gmsh::model::add("t4");

  double cm = 1e-02;
  double e1 = 4.5 * cm, e2 = 6 * cm / 2, e3 = 5 * cm / 2;
  double h1 = 5 * cm, h2 = 10 * cm, h3 = 5 * cm, h4 = 2 * cm, h5 = 4.5 * cm;
  double R1 = 1 * cm, R2 = 1.5 * cm, r = 1 * cm;
  double Lc1 = 0.01;
  double Lc2 = 0.003;

  double ccos =
    (-h5 * R1 + e2 * hypot(h5, hypot(e2, R1))) / (h5 * h5 + e2 * e2);
  double ssin = sqrt(1 - ccos * ccos);

  // We start by defining some points and some lines. To make the code shorter
  // we can redefine a namespace:
  namespace factory = gmsh::model::geo;
  factory::addPoint(-e1 - e2, 0, 0, Lc1, 1);
  factory::addPoint(-e1 - e2, h1, 0, Lc1, 2);
  factory::addPoint(-e3 - r, h1, 0, Lc2, 3);
  factory::addPoint(-e3 - r, h1 + r, 0, Lc2, 4);
  factory::addPoint(-e3, h1 + r, 0, Lc2, 5);
  factory::addPoint(-e3, h1 + h2, 0, Lc1, 6);
  factory::addPoint(e3, h1 + h2, 0, Lc1, 7);
  factory::addPoint(e3, h1 + r, 0, Lc2, 8);
  factory::addPoint(e3 + r, h1 + r, 0, Lc2, 9);
  factory::addPoint(e3 + r, h1, 0, Lc2, 10);
  factory::addPoint(e1 + e2, h1, 0, Lc1, 11);
  factory::addPoint(e1 + e2, 0, 0, Lc1, 12);
  factory::addPoint(e2, 0, 0, Lc1, 13);

  factory::addPoint(R1 / ssin, h5 + R1 * ccos, 0, Lc2, 14);
  factory::addPoint(0, h5, 0, Lc2, 15);
  factory::addPoint(-R1 / ssin, h5 + R1 * ccos, 0, Lc2, 16);
  factory::addPoint(-e2, 0.0, 0, Lc1, 17);

  factory::addPoint(-R2, h1 + h3, 0, Lc2, 18);
  factory::addPoint(-R2, h1 + h3 + h4, 0, Lc2, 19);
  factory::addPoint(0, h1 + h3 + h4, 0, Lc2, 20);
  factory::addPoint(R2, h1 + h3 + h4, 0, Lc2, 21);
  factory::addPoint(R2, h1 + h3, 0, Lc2, 22);
  factory::addPoint(0, h1 + h3, 0, Lc2, 23);

  factory::addPoint(0, h1 + h3 + h4 + R2, 0, Lc2, 24);
  factory::addPoint(0, h1 + h3 - R2, 0, Lc2, 25);

  factory::addLine(1, 17, 1);
  factory::addLine(17, 16, 2);

  // Gmsh provides other curve primitives than straight lines: splines,
  // B-splines, circle arcs, ellipse arcs, etc. Here we define a new circle arc,
  // starting at point 14 and ending at point 16, with the circle's center being
  // the point 15:
  factory::addCircleArc(14, 15, 16, 3);

  // Note that, in Gmsh, circle arcs should always be smaller than Pi. The
  // OpenCASCADE geometry kernel does not have this limitation.

  // We can then define additional lines and circles, as well as a new surface:
  factory::addLine(14, 13, 4);
  factory::addLine(13, 12, 5);
  factory::addLine(12, 11, 6);
  factory::addLine(11, 10, 7);
  factory::addCircleArc(8, 9, 10, 8);
  factory::addLine(8, 7, 9);
  factory::addLine(7, 6, 10);
  factory::addLine(6, 5, 11);
  factory::addCircleArc(3, 4, 5, 12);
  factory::addLine(3, 2, 13);
  factory::addLine(2, 1, 14);
  factory::addLine(18, 19, 15);
  factory::addCircleArc(21, 20, 24, 16);
  factory::addCircleArc(24, 20, 19, 17);
  factory::addCircleArc(18, 23, 25, 18);
  factory::addCircleArc(25, 23, 22, 19);
  factory::addLine(21, 22, 20);

  factory::addCurveLoop({17, -15, 18, 19, -20, 16}, 21);
  factory::addPlaneSurface({21}, 22);

  // But we still need to define the exterior surface. Since this surface has a
  // hole, its definition now requires two curves loops:
  factory::addCurveLoop({11, -12, 13, 14, 1, 2, -3, 4, 5, 6, 7, -8, 9, 10}, 23);
  factory::addPlaneSurface({23, 21}, 24);

  // As a general rule, if a surface has N holes, it is defined by N+1 curve
  // loops: the first loop defines the exterior boundary; the other loops define
  // the boundaries of the holes.

  factory::synchronize();

  // Finally, we can add some comments by creating a post-processing view
  // containing some strings:
  int v = gmsh::view::add("comments");

  // Add a text string in window coordinates, 10 pixels from the left and 10
  // pixels from the bottom:
  gmsh::view::addListDataString(v, {10, -10}, {"Created with Gmsh"});

  // Add a text string in model coordinates centered at (X,Y,Z) = (0, 0.11, 0),
  // with some style attributes:
  gmsh::view::addListDataString(v, {0, 0.11, 0}, {"Hole"},
                                {"Align", "Center", "Font", "Helvetica"});

  // If a string starts with `file://', the rest is interpreted as an image
  // file. For 3D annotations, the size in model coordinates can be specified
  // after a `@' symbol in the form `widthxheight' (if one of `width' or
  // `height' is zero, natural scaling is used; if both are zero, original image
  // dimensions in pixels are used):
  gmsh::view::addListDataString(
    v, {0, 0.09, 0}, {"file://../t4_image.png@0.01x0"}, {"Align", "Center"});

  // The 3D orientation of the image can be specified by proving the direction
  // of the bottom and left edge of the image in model space:
  gmsh::view::addListDataString(v, {-0.01, 0.09, 0},
                                {"file://../t4_image.png@0.01x0,0,0,1,0,1,0"});

  // The image can also be drawn in "billboard" mode, i.e. always parallel to
  // the camera, by using the `#' symbol:
  gmsh::view::addListDataString(
    v, {0, 0.12, 0}, {"file://../t4_image.png@0.01x0#"}, {"Align", "Center"});

  // The size of 2D annotations is given directly in pixels:
  gmsh::view::addListDataString(v, {150, -7}, {"file://../t4_image.png@20x0"});

  // These annotations are handled by a list-based post-processing view. For
  // large post-processing datasets, that contain actual field values defined on
  // a mesh, you should use model-based post-processing views instead, which
  // allow to efficiently store continuous or discontinuous scalar, vector and
  // tensor fields, or arbitrary polynomial order.

  // Views and geometrical entities can be made to respond to double-click
  // events, here to print some messages to the console:
  gmsh::view::option::setString(v, "DoubleClickedCommand",
                                "Printf('View[0] has been double-clicked!');");
  gmsh::option::setString("Geometry.DoubleClickedLineCommand",
                          "Printf('Curve %g has been double-clicked!', "
                          "Geometry.DoubleClickedEntityTag);");

  // We can also change the color of some entities:
  gmsh::model::setColor({{2, 22}}, 127, 127, 127); // Gray50
  gmsh::model::setColor({{2, 24}}, 160, 32, 240); // Purple
  for(int i = 1; i <= 14; i++)
    gmsh::model::setColor({{1, i}}, 255, 0, 0); // Red
  for(int i = 15; i <= 20; i++)
    gmsh::model::setColor({{1, i}}, 255, 255, 0); // Yellow

  gmsh::model::mesh::generate(2);

  gmsh::write("t4.msh");

  // Launch the GUI to see the results:
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
