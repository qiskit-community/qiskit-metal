// -----------------------------------------------------------------------------
//
//  Gmsh C++ tutorial 20
//
//  STEP import and manipulation, geometry partitioning
//
// -----------------------------------------------------------------------------

// The OpenCASCADE CAD kernel allows to import STEP files and to modify them. In
// this tutorial we will load a STEP geometry and partition it into slices.

#include <set>
#include <cmath>
#include <cstdlib>
#include <algorithm>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  gmsh::model::add("t20");

  // Load a STEP file (using `importShapes' instead of `merge' allows to
  // directly retrieve the tags of the highest dimensional imported entities):
  std::vector<std::pair<int, int> > v;
  try {
    gmsh::model::occ::importShapes("../t20_data.step", v);
  } catch(...) {
    gmsh::logger::write("Could not load STEP file: bye!");
    gmsh::finalize();
    return 0;
  }

  // If we had specified
  //
  // gmsh::option::setString("Geometry.OCCTargetUnit", "M");
  //
  // before merging the STEP file, OpenCASCADE would have converted the units to
  // meters (instead of the default, which is millimeters).

  // Get the bounding box of the volume:
  double xmin, ymin, zmin, xmax, ymax, zmax;
  gmsh::model::occ::getBoundingBox(v[0].first, v[0].second, xmin, ymin, zmin,
                                   xmax, ymax, zmax);

  // We want to slice the model into N slices, and either keep the volume slices
  // or just the surfaces obtained by the cutting:

  int N = 5; // Number of slices
  std::string dir = "X"; // Direction: "X", "Y" or "Z"
  bool surf = false; // Keep only surfaces?

  double dx = (xmax - xmin);
  double dy = (ymax - ymin);
  double dz = (zmax - zmin);
  double L = (dir == "X") ? dz : dx;
  double H = (dir == "Y") ? dz : dy;

  // Create the first cutting plane
  std::vector<std::pair<int, int> > s;
  s.push_back({2, gmsh::model::occ::addRectangle(xmin, ymin, zmin, L, H)});
  if(dir == "X") {
    gmsh::model::occ::rotate({s[0]}, xmin, ymin, zmin, 0, 1, 0, -M_PI / 2);
  }
  else if(dir == "Y") {
    gmsh::model::occ::rotate({s[0]}, xmin, ymin, zmin, 1, 0, 0, M_PI / 2);
  }
  double tx = (dir == "X") ? dx / N : 0;
  double ty = (dir == "Y") ? dy / N : 0;
  double tz = (dir == "Z") ? dz / N : 0;
  gmsh::model::occ::translate({s[0]}, tx, ty, tz);

  // Create the other cutting planes:
  std::vector<std::pair<int, int> > tmp;
  for(int i = 1; i < N - 1; i++) {
    gmsh::model::occ::copy({s[0]}, tmp);
    s.push_back(tmp[0]);
    gmsh::model::occ::translate({s.back()}, i * tx, i * ty, i * tz);
  }

  // Fragment (i.e. intersect) the volume with all the cutting planes:
  std::vector<std::pair<int, int> > ov;
  std::vector<std::vector<std::pair<int, int> > > ovv;
  gmsh::model::occ::fragment(v, s, ov, ovv);

  // Now remove all the surfaces (and their bounding entities) that are not on
  // the boundary of a volume, i.e. the parts of the cutting planes that "stick
  // out" of the volume:
  gmsh::model::occ::getEntities(tmp, 2);
  gmsh::model::occ::remove(tmp, true);

  gmsh::model::occ::synchronize();

  if(surf) {
    // If we want to only keep the surfaces, retrieve the surfaces in bounding
    // boxes around the cutting planes...
    double eps = 1e-4;
    std::vector<std::pair<int, int> > s;
    for(int i = 1; i < N; i++) {
      double xx = (dir == "X") ? xmin : xmax;
      double yy = (dir == "Y") ? ymin : ymax;
      double zz = (dir == "Z") ? zmin : zmax;
      std::vector<std::pair<int, int> > e;
      gmsh::model::getEntitiesInBoundingBox(
        xmin - eps + i * tx, ymin - eps + i * ty, zmin - eps + i * tz,
        xx + eps + i * tx, yy + eps + i * ty, zz + eps + i * tz, e, 2);
      s.insert(s.end(), e.begin(), e.end());
    }
    // ...and remove all the other entities (here directly in the model, as we
    // won't modify any OpenCASCADE entities later on):
    std::vector<std::pair<int, int> > dels;
    gmsh::model::getEntities(dels, 2);
    for(auto it = s.begin(); it != s.end(); ++it) {
      auto it2 = std::find(dels.begin(), dels.end(), *it);
      if(it2 != dels.end()) dels.erase(it2);
    }
    gmsh::model::getEntities(tmp, 3);
    gmsh::model::removeEntities(tmp);
    gmsh::model::removeEntities(dels);
    gmsh::model::getEntities(tmp, 1);
    gmsh::model::removeEntities(tmp);
    gmsh::model::getEntities(tmp, 0);
    gmsh::model::removeEntities(tmp);
  }

  // Finally, let's specify a global mesh size and mesh the partitioned model:
  gmsh::option::setNumber("Mesh.MeshSizeMin", 3);
  gmsh::option::setNumber("Mesh.MeshSizeMax", 3);
  gmsh::model::mesh::generate(3);
  gmsh::write("t20.msh");

  // Launch the GUI to see the results:
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
