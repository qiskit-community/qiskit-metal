// -----------------------------------------------------------------------------
//
//  Gmsh C++ extended tutorial 5
//
//  Additional geometrical data: parametrizations, normals, curvatures
//
// -----------------------------------------------------------------------------

#include <set>
#include <algorithm>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  // The API provides access to geometrical data in a CAD kernel agnostic
  // manner.

  // Let's create a simple CAD model by fusing a sphere and a cube, then mesh
  // the surfaces:
  gmsh::model::add("x5");
  int s = gmsh::model::occ::addSphere(0, 0, 0, 1);
  int b = gmsh::model::occ::addBox(0.5, 0, 0, 1.3, 2, 3);
  std::vector<std::pair<int, int> > ov;
  std::vector<std::vector<std::pair<int, int> > > ovv;
  gmsh::model::occ::fuse({{3, s}}, {{3, b}}, ov, ovv);
  gmsh::model::occ::synchronize();
  gmsh::model::mesh::generate(2);

  // We can for example retrieve the exact normals and the curvature at all the
  // mesh nodes (i.e. not normals and curvatures computed from the mesh, but
  // directly evaluated on the geometry), by querying the CAD kernels at the
  // corresponding parametric coordinates.
  std::vector<double> normals, curvatures;

  // For each surface in the model:
  std::vector<std::pair<int, int> > entities;
  gmsh::model::getEntities(entities, 2);
  for(auto e : entities) {
    // Retrieve the surface tag
    int s = e.second;

    // Get the mesh nodes on the surface, including those on the boundary
    // (contrary to internal nodes, which store their parametric coordinates,
    // boundary nodes will be reparametrized on the surface in order to compute
    // their parametric coordinates, the result being different when
    // reparametrized on another adjacent surface)
    std::vector<std::size_t> tags;
    std::vector<double> coord, param;
    gmsh::model::mesh::getNodes(tags, coord, param, 2, s, true);

    // Get the surface normals on all the points on the surface corresponding to
    // the parametric coordinates of the nodes
    std::vector<double> norm;
    gmsh::model::getNormal(s, param, norm);

    // In the same way, get the curvature
    std::vector<double> curv;
    gmsh::model::getCurvature(2, s, param, curv);

    // Store the normals and the curvatures so that we can display them as
    // list-based post-processing views
    for(std::size_t i = 0; i < coord.size(); i += 3) {
      normals.push_back(coord[i]);
      normals.push_back(coord[i + 1]);
      normals.push_back(coord[i + 2]);
      normals.push_back(norm[i]);
      normals.push_back(norm[i + 1]);
      normals.push_back(norm[i + 2]);
      curvatures.push_back(coord[i]);
      curvatures.push_back(coord[i + 1]);
      curvatures.push_back(coord[i + 2]);
      curvatures.push_back(curv[i / 3]);
    }
  }

  // Create a list-based vector view on points to display the normals, and a
  // scalar view on points to display the curvatures
  int vn = gmsh::view::add("normals");
  gmsh::view::addListData(vn, "VP", normals.size() / 6, normals);
  int vc = gmsh::view::add("curvatures");
  gmsh::view::addListData(vc, "SP", curvatures.size() / 4, curvatures);

  // We can also retrieve the parametrization bounds of model entities, e.g. of
  // curve 5, and evaluate the parametrization for several parameter values:
  std::vector<double> bounds[2], t, xyz1;
  gmsh::model::getParametrizationBounds(1, 5, bounds[0], bounds[1]);
  int N = 20;
  for(int i = 0; i < N; i++)
    t.push_back(bounds[0][0] + i * (bounds[1][0] - bounds[0][0]) / N);
  gmsh::model::getValue(1, 5, t, xyz1);

  // We can also reparametrize curve 5 on surface 1, and evaluate the points in
  // the parametric plane of the surface:
  std::vector<double> uv, xyz2;
  gmsh::model::reparametrizeOnSurface(1, 5, t, 1, uv);
  gmsh::model::getValue(2, 1, uv, xyz2);

  // Hopefully we get the same x, y, z coordinates!
  std::vector<double> diff(xyz1.size());
  std::transform(xyz1.begin(), xyz1.end(), xyz2.begin(), diff.begin(),
                 [](double a, double b){ return std::abs(a - b); });
  if(*std::max_element(diff.begin(), diff.end()) < 1e-12)
    gmsh::logger::write("Evaluation on curve and surface match!");
  else
    gmsh::logger::write("Evaluation on curve and surface do not match!",
                        "error");

  // Launch the GUI to see the results:
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
