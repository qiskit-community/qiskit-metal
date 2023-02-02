#include <cstdio>
#include <gmsh.h>
#include <set>

int main(int argc, char **argv)
{
  // initialize Gmsh
  gmsh::initialize(argc, argv);

  // create a new Gmsh model
  gmsh::model::add("my test model");

  // create three surfaces using the OpenCASCADE CAD kernel
  int s1 = gmsh::model::occ::addRectangle(0, 0, 0, 1, 1);
  int s2 = gmsh::model::occ::addRectangle(1, 0, 0, 1, 1);
  int s3 = gmsh::model::occ::addDisk(1.5, 0.5, 0, 0.25, 0.25);

  // fragment all surfaces to have a conformal, non-overlapping geometry
  std::vector<std::pair<int, int> > ov;
  std::vector<std::vector<std::pair<int, int> > > ovv;
  gmsh::model::occ::fragment({{2, s1}, {2, s2}, {2, s3}}, {}, ov, ovv);

  // synchronize the CAD model with the Gmsh model
  gmsh::model::occ::synchronize();

  // generate 2D mesh
  gmsh::model::mesh::generate(2);

  // explore the mesh: what type of 2D elements do we have?
  std::vector<int> eleTypes;
  gmsh::model::mesh::getElementTypes(eleTypes, 2);
  if(eleTypes.size() != 1) {
    gmsh::logger::write("Hybrid meshes not handled in this example!", "error");
    return 1;
  }
  int eleType2D = eleTypes[0];
  std::string name;
  int dim, order, numNodes, numPrimaryNodes;
  std::vector<double> paramCoord;
  gmsh::model::mesh::getElementProperties(eleType2D, name, dim, order, numNodes,
                                          paramCoord, numPrimaryNodes);
  gmsh::logger::write("2D elements are of type '" + name +
                      "' (type = " + std::to_string(eleType2D) + ") ");

  // iterate over all surfaces, get the 2D elements and create new 1D elements
  // for all edges
  std::vector<std::pair<int, int> > entities;
  gmsh::model::getEntities(entities, 2);
  for(std::size_t i = 0; i < entities.size(); i++) {
    int s = entities[i].second;
    std::vector<std::size_t> elementTags, nodeTags;
    gmsh::model::mesh::getElementsByType(eleType2D, elementTags, nodeTags, s);
    gmsh::logger::write("- " + std::to_string(elementTags.size()) +
                        " elements in surface " + std::to_string(s));

    // get the nodes on the edges of the 2D elements
    std::vector<std::size_t> nodes;
    gmsh::model::mesh::getElementEdgeNodes(eleType2D, nodes, s);

    // create a new discrete entity of dimension 1
    int c = gmsh::model::addDiscreteEntity(1);

    // and add new 1D elements to it, for all edges
    int eleType1D = gmsh::model::mesh::getElementType("line", order);
    gmsh::model::mesh::addElementsByType(c, eleType1D, {}, nodes);

    // this will create two 1D elements for each edge; to create unique elements
    // it would be useful to call getElementEdgeNodes() with the extra `primary'
    // argument set to 'true' (to only get start/end nodes even in the
    // high-order case, i.e. consider topological edges), then sort them and
    // make them unique.

    // this could be enriched with additional info: each topological edge could
    // be associated with the tag of its parent element; in the sorting process
    // (eliminating duplicates) a second tag can be associated for internal
    // edges, allowing to keep track of neighbors
  }

  // gmsh::write("edges.msh");

  // iterate over all 1D elements and get integration information
  gmsh::model::mesh::getElementTypes(eleTypes, 1);
  int eleType1D = eleTypes[0];
  std::vector<double> uvw, q;
  gmsh::model::mesh::getIntegrationPoints(eleType1D, "Gauss3", uvw, q);
  std::vector<double> bf;
  int numComp, numOrientations;
  gmsh::model::mesh::getBasisFunctions(eleType1D, uvw, "Lagrange", numComp, bf,
                                       numOrientations);
  gmsh::model::getEntities(entities, 1);
  for(std::size_t i = 0; i < entities.size(); i++) {
    int c = entities[i].second;
    std::vector<std::size_t> elementTags, nodeTags;
    gmsh::model::mesh::getElementsByType(eleType1D, elementTags, nodeTags, c);
    gmsh::logger::write("- " + std::to_string(elementTags.size()) +
                        " elements on curve " + std::to_string(c));
    std::vector<double> jac, det, pts;
    gmsh::model::mesh::getJacobians(eleType1D, uvw, jac, det, pts, c);
  }

  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
