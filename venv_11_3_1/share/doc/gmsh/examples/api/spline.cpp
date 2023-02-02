#include <gmsh.h>
#include <set>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  gmsh::model::add("spline");

  for(unsigned int i = 1; i < 11; i++)
    gmsh::model::occ::addPoint(i + 1, sin(i / 9. * 2. * M_PI), 0, 0.1, i);

  gmsh::model::occ::addSpline({1, 2, 3, 4, 5, 6, 7, 8, 9, 10}, 1);
  gmsh::model::occ::addBSpline({1, 2, 3, 4, 5, 6, 7, 8, 9, 10}, 2);
  gmsh::model::occ::addBezier({1, 2, 3, 4, 5, 6, 7, 8, 9, 10}, 3);

  gmsh::model::occ::addPoint(0.2, -1.6, 0, 0.1, 101);
  gmsh::model::occ::addPoint(1.2, -1.6, 0, 0.1, 102);
  gmsh::model::occ::addPoint(1.2, -1.1, 0, 0.1, 103);
  gmsh::model::occ::addPoint(0.3, -1.1, 0, 0.1, 104);
  gmsh::model::occ::addPoint(0.7, -1, 0, 0.1, 105);

  // periodic bspline through the control points
  gmsh::model::occ::addSpline({103, 102, 101, 104, 105, 103}, 100);

  // periodic bspline from given control points and default parameters - will
  // create a new vertex
  gmsh::model::occ::addBSpline({103, 102, 101, 104, 105, 103}, 101);

  // general bspline with explicit degree, knots and multiplicities
  gmsh::model::occ::addPoint(0, -2, 0, 0.1, 201);
  gmsh::model::occ::addPoint(1, -2, 0, 0.1, 202);
  gmsh::model::occ::addPoint(1, -3, 0, 0.1, 203);
  gmsh::model::occ::addPoint(0, -3, 0, 0.1, 204);
  gmsh::model::occ::addBSpline({201, 202, 203, 204}, 200, 2, {}, {0, 0.5, 1},
                               {3, 1, 3});

  gmsh::model::occ::synchronize();

  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
