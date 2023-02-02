// -----------------------------------------------------------------------------
//
//  Gmsh C++ extended tutorial 2
//
//  Mesh import, discrete entities, hybrid models, terrain meshing
//
// -----------------------------------------------------------------------------

#include <set>
#include <iostream>
#include <gmsh.h>

// The API can be used to import a mesh without reading it from a file, by
// creating nodes and elements on the fly and storing them in model
// entities. These model entities can be existing CAD entities, or can be
// discrete entities, entirely defined by the mesh.
//
// Discrete entities can be reparametrized (see `t13.py') so that they can be
// remeshed later on; and they can also be combined with built-in CAD entities
// to produce hybrid models.
//
// We combine all these features in this tutorial to perform terrain meshing,
// where the terrain is described by a discrete surface (that we then
// reparametrize) combined with a CAD representation of the underground.

int main(int argc, char **argv)
{
  gmsh::initialize();

  gmsh::model::add("x2");

  // We will create the terrain surface mesh from N x N input data points:
  int N = 100;

  // Helper function to return a node tag given two indices i and j:
  auto tag = [N](std::size_t i, std::size_t j) { return (N + 1) * i + j + 1; };

  // The x, y, z coordinates of all the points:
  std::vector<double> coords;

  // The tags of the corresponding nodes:
  std::vector<std::size_t> nodes;

  // The connectivities of the triangle elements (3 node tags per triangle) on
  // the terrain surface:
  std::vector<std::size_t> tris;

  // The connectivities of the line elements on the 4 boundaries (2 node tags
  // for each line element):
  std::vector<std::size_t> lin[4];

  // The connectivities of the point elements on the 4 corners (1 node tag for
  // each point element):
  std::size_t pnt[4] = {tag(0, 0), tag(N, 0), tag(N, N), tag(0, N)};

  for(std::size_t i = 0; i < N + 1; i++) {
    for(std::size_t j = 0; j < N + 1; j++) {
      nodes.push_back(tag(i, j));
      coords.insert(coords.end(), {(double)i / N, (double)j / N,
                                   0.05 * sin(10 * (double)(i + j) / N)});
      if(i > 0 && j > 0) {
        tris.insert(tris.end(),
                    {tag(i - 1, j - 1), tag(i, j - 1), tag(i - 1, j)});
        tris.insert(tris.end(), {tag(i, j - 1), tag(i, j), tag(i - 1, j)});
      }
      if((i == 0 || i == N) && j > 0) {
        std::size_t s = (i == 0) ? 3 : 1;
        lin[s].insert(lin[s].end(), {tag(i, j - 1), tag(i, j)});
      }
      if((j == 0 || j == N) && i > 0) {
        std::size_t s = (j == 0) ? 0 : 2;
        lin[s].insert(lin[s].end(), {tag(i - 1, j), tag(i, j)});
      }
    }
  }

  // Create 4 discrete points for the 4 corners of the terrain surface:
  for(int i = 0; i < 4; i++) gmsh::model::addDiscreteEntity(0, i + 1);
  gmsh::model::setCoordinates(1, 0, 0, coords[3 * tag(0, 0) - 1]);
  gmsh::model::setCoordinates(2, 1, 0, coords[3 * tag(N, 0) - 1]);
  gmsh::model::setCoordinates(3, 1, 1, coords[3 * tag(N, N) - 1]);
  gmsh::model::setCoordinates(4, 0, 1, coords[3 * tag(0, N) - 1]);

  // Create 4 discrete bounding curves, with their boundary points:
  for(int i = 0; i < 4; i++)
    gmsh::model::addDiscreteEntity(1, i + 1, {i + 1, (i < 3) ? (i + 2) : 1});

  // Create one discrete surface, with its bounding curves:
  gmsh::model::addDiscreteEntity(2, 1, {1, 2, -3, -4});

  // Add all the nodes on the surface (for simplicity... see below):
  gmsh::model::mesh::addNodes(2, 1, nodes, coords);

  // Add point elements on the 4 points, line elements on the 4 curves, and
  // triangle elements on the surface:
  for(int i = 0; i < 4; i++) {
    // Type 15 for point elements:
    gmsh::model::mesh::addElementsByType(i + 1, 15, {}, {pnt[i]});
    // Type 1 for 2-node line elements:
    gmsh::model::mesh::addElementsByType(i + 1, 1, {}, lin[i]);
  }
  // Type 2 for 3-node triangle elements:
  gmsh::model::mesh::addElementsByType(1, 2, {}, tris);

  // Reclassify the nodes on the curves and the points (since we put them all on
  // the surface before with `addNodes' for simplicity)
  gmsh::model::mesh::reclassifyNodes();

  // Create a geometry for the discrete curves and surfaces, so that we can
  // remesh them later on:
  gmsh::model::mesh::createGeometry();

  // Note that for more complicated meshes, e.g. for on input unstructured STL
  // mesh, we could use `classifySurfaces()' to automatically create the
  // discrete entities and the topology; but we would then have to extract the
  // boundaries afterwards.

  // Create other CAD entities to form one volume below the terrain surface.
  // Beware that only built-in CAD entities can be hybrid, i.e. have discrete
  // entities on their boundary: OpenCASCADE does not support this feature.
  int p1 = gmsh::model::geo::addPoint(0, 0, -0.5);
  int p2 = gmsh::model::geo::addPoint(1, 0, -0.5);
  int p3 = gmsh::model::geo::addPoint(1, 1, -0.5);
  int p4 = gmsh::model::geo::addPoint(0, 1, -0.5);
  int c1 = gmsh::model::geo::addLine(p1, p2);
  int c2 = gmsh::model::geo::addLine(p2, p3);
  int c3 = gmsh::model::geo::addLine(p3, p4);
  int c4 = gmsh::model::geo::addLine(p4, p1);
  int c10 = gmsh::model::geo::addLine(p1, 1);
  int c11 = gmsh::model::geo::addLine(p2, 2);
  int c12 = gmsh::model::geo::addLine(p3, 3);
  int c13 = gmsh::model::geo::addLine(p4, 4);
  int ll1 = gmsh::model::geo::addCurveLoop({c1, c2, c3, c4});
  int s1 = gmsh::model::geo::addPlaneSurface({ll1});
  int ll3 = gmsh::model::geo::addCurveLoop({c1, c11, -1, -c10});
  int s3 = gmsh::model::geo::addPlaneSurface({ll3});
  int ll4 = gmsh::model::geo::addCurveLoop({c2, c12, -2, -c11});
  int s4 = gmsh::model::geo::addPlaneSurface({ll4});
  int ll5 = gmsh::model::geo::addCurveLoop({c3, c13, 3, -c12});
  int s5 = gmsh::model::geo::addPlaneSurface({ll5});
  int ll6 = gmsh::model::geo::addCurveLoop({c4, c10, 4, -c13});
  int s6 = gmsh::model::geo::addPlaneSurface({ll6});
  int sl1 = gmsh::model::geo::addSurfaceLoop({s1, s3, s4, s5, s6, 1});
  int v1 = gmsh::model::geo::addVolume({sl1});
  gmsh::model::geo::synchronize();

  // Set this to true to build a fully hex mesh:
  bool transfinite = false;
  bool transfiniteAuto = false;

  if(transfinite) {
    int NN = 30;
    std::vector<std::pair<int, int> > tmp;
    gmsh::model::getEntities(tmp, 1);
    for(auto c : tmp) { gmsh::model::mesh::setTransfiniteCurve(c.second, NN); }
    gmsh::model::getEntities(tmp, 2);
    for(auto s : tmp) {
      gmsh::model::mesh::setTransfiniteSurface(s.second);
      gmsh::model::mesh::setRecombine(s.first, s.second);
      gmsh::model::mesh::setSmoothing(s.first, s.second, 100);
    }
    gmsh::model::mesh::setTransfiniteVolume(v1);
  }
  else if(transfiniteAuto) {
    gmsh::option::setNumber("Mesh.MeshSizeMin", 0.5);
    gmsh::option::setNumber("Mesh.MeshSizeMax", 0.5);
    // setTransfiniteAutomatic() uses the sizing constraints to set the number
    // of points
    gmsh::model::mesh::setTransfiniteAutomatic();
  }
  else {
    gmsh::option::setNumber("Mesh.MeshSizeMin", 0.05);
    gmsh::option::setNumber("Mesh.MeshSizeMax", 0.05);
  }

  gmsh::model::mesh::generate(3);
  gmsh::write("x2.msh");

  // Launch the GUI to see the results:
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
