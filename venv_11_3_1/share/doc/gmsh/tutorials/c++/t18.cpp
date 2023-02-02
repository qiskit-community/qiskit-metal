// -----------------------------------------------------------------------------
//
//  Gmsh C++ tutorial 18
//
//  Periodic meshes
//
// -----------------------------------------------------------------------------

// Periodic meshing constraints can be imposed on surfaces and curves.

#include <set>
#include <algorithm>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  gmsh::model::add("t18");

  // Let's use the OpenCASCADE geometry kernel to build two geometries.

  // The first geometry is very simple: a unit cube with a non-uniform mesh size
  // constraint (set on purpose to be able to verify visually that the
  // periodicity constraint works!):

  gmsh::model::occ::addBox(0, 0, 0, 1, 1, 1, 1);
  gmsh::model::occ::synchronize();

  std::vector<std::pair<int, int> > out;
  gmsh::model::getEntities(out, 0);
  gmsh::model::mesh::setSize(out, 0.1);
  gmsh::model::mesh::setSize({{0, 1}}, 0.02);

  // To impose that the mesh on surface 2 (the right side of the cube) should
  // match the mesh from surface 1 (the left side), the following periodicity
  // constraint is set:
  std::vector<double> translation(
    {1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1});
  gmsh::model::mesh::setPeriodic(2, {2}, {1}, translation);

  // The periodicity transform is provided as a 4x4 affine transformation
  // matrix, given by row.

  // During mesh generation, the mesh on surface 2 will be created by copying
  // the mesh from surface 1.

  // Multiple periodicities can be imposed in the same way:
  gmsh::model::mesh::setPeriodic(
    2, {6}, {5}, {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1});
  gmsh::model::mesh::setPeriodic(
    2, {4}, {3}, {1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1});

  // For more complicated cases, finding the corresponding surfaces by hand can
  // be tedious, especially when geometries are created through solid
  // modelling. Let's construct a slightly more complicated geometry.

  // We start with a cube and some spheres:
  gmsh::model::occ::addBox(2, 0, 0, 1, 1, 1, 10);
  double x = 2 - 0.3, y = 0, z = 0;
  gmsh::model::occ::addSphere(x, y, z, 0.35, 11);
  gmsh::model::occ::addSphere(x + 1, y, z, 0.35, 12);
  gmsh::model::occ::addSphere(x, y + 1, z, 0.35, 13);
  gmsh::model::occ::addSphere(x, y, z + 1, 0.35, 14);
  gmsh::model::occ::addSphere(x + 1, y + 1, z, 0.35, 15);
  gmsh::model::occ::addSphere(x, y + 1, z + 1, 0.35, 16);
  gmsh::model::occ::addSphere(x + 1, y, z + 1, 0.35, 17);
  gmsh::model::occ::addSphere(x + 1, y + 1, z + 1, 0.35, 18);

  // We first fragment all the volumes, which will leave parts of spheres
  // protruding outside the cube:
  std::vector<std::vector<std::pair<int, int> > > out_map;
  std::vector<std::pair<int, int> > sph;
  for(int i = 11; i <= 18; i++) sph.push_back(std::pair<int, int>(3, i));
  gmsh::model::occ::fragment({{3, 10}}, sph, out, out_map);
  gmsh::model::occ::synchronize();

  // Ask OpenCASCADE to compute more accurate bounding boxes of entities using
  // the STL mesh:
  gmsh::option::setNumber("Geometry.OCCBoundsUseStl", 1);

  // We then retrieve all the volumes in the bounding box of the original cube,
  // and delete all the parts outside it:
  double eps = 1e-3;
  std::vector<std::pair<int, int> > in;
  gmsh::model::getEntitiesInBoundingBox(2 - eps, -eps, -eps, 2 + 1 + eps,
                                        1 + eps, 1 + eps, in, 3);
  for(auto i : in) {
    auto it = std::find(out.begin(), out.end(), i);
    if(it != out.end()) out.erase(it);
  }
  gmsh::model::removeEntities(out, true); // Delete outside parts recursively

  // We now set a non-uniform mesh size constraint (again to check results
  // visually):
  std::vector<std::pair<int, int> > p;
  gmsh::model::getBoundary(in, p, false, false, true); // Get all points
  gmsh::model::mesh::setSize(p, 0.1);
  gmsh::model::getEntitiesInBoundingBox(2 - eps, -eps, -eps, 2 + eps, eps, eps,
                                        p, 0);
  gmsh::model::mesh::setSize(p, 0.001);

  // We now identify corresponding surfaces on the left and right sides of the
  // geometry automatically.

  // First we get all surfaces on the left:
  std::vector<std::pair<int, int> > sxmin;
  gmsh::model::getEntitiesInBoundingBox(2 - eps, -eps, -eps, 2 + eps, 1 + eps,
                                        1 + eps, sxmin, 2);
  for(auto i : sxmin) {
    // Then we get the bounding box of each left surface
    double xmin, ymin, zmin, xmax, ymax, zmax;
    gmsh::model::getBoundingBox(i.first, i.second, xmin, ymin, zmin, xmax, ymax,
                                zmax);
    // We translate the bounding box to the right and look for surfaces inside
    // it:
    std::vector<std::pair<int, int> > sxmax;
    gmsh::model::getEntitiesInBoundingBox(xmin - eps + 1, ymin - eps,
                                          zmin - eps, xmax + eps + 1,
                                          ymax + eps, zmax + eps, sxmax, 2);
    // For all the matches, we compare the corresponding bounding boxes...
    for(auto j : sxmax) {
      double xmin2, ymin2, zmin2, xmax2, ymax2, zmax2;
      gmsh::model::getBoundingBox(j.first, j.second, xmin2, ymin2, zmin2, xmax2,
                                  ymax2, zmax2);
      xmin2 -= 1;
      xmax2 -= 1;
      // ...and if they match, we apply the periodicity constraint
      if(std::abs(xmin2 - xmin) < eps && std::abs(xmax2 - xmax) < eps &&
         std::abs(ymin2 - ymin) < eps && std::abs(ymax2 - ymax) < eps &&
         std::abs(zmin2 - zmin) < eps && std::abs(zmax2 - zmax) < eps) {
        gmsh::model::mesh::setPeriodic(2, {j.second}, {i.second}, translation);
      }
    }
  }

  gmsh::model::mesh::generate(3);
  gmsh::write("t18.msh");

  // Launch the GUI to see the results:
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
