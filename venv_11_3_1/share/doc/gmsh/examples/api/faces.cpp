#include <cstdio>
#include <gmsh.h>
#include <set>

int main(int argc, char **argv)
{
  // initialize Gmsh
  gmsh::initialize(argc, argv);

  // create a new Gmsh model
  gmsh::model::add("my test model");

  // create three solids using the OpenCASCADE CAD kernel
  int v1 = gmsh::model::occ::addBox(0, 0, 0, 1, 1, 1);
  int v2 = gmsh::model::occ::addBox(1, 0, 0, 1, 1, 1);
  int v3 = gmsh::model::occ::addSphere(1.5, 0.5, 0.5, 0.25);

  // fragment all volumes to have a conformal, non-overlapping geometry
  std::vector<std::pair<int, int> > ov;
  std::vector<std::vector<std::pair<int, int> > > ovv;
  gmsh::model::occ::fragment({{3, v1}, {3, v2}, {3, v3}}, {}, ov, ovv);

  // synchronize the CAD model with the Gmsh model
  gmsh::model::occ::synchronize();

  // generate 3D mesh
  gmsh::model::mesh::generate(3);

  // explore the mesh: what type of 3D elements do we have?
  std::vector<int> eleTypes;
  gmsh::model::mesh::getElementTypes(eleTypes, 3);
  if(eleTypes.size() != 1) {
    gmsh::logger::write("Hybrid meshes not handled in this example!", "error");
    return 1;
  }
  int eleType3D = eleTypes[0];
  std::string name;
  int dim, order, numNodes, numPrimaryNodes;
  std::vector<double> paramCoord;
  gmsh::model::mesh::getElementProperties(eleType3D, name, dim, order, numNodes,
                                          paramCoord, numPrimaryNodes);
  gmsh::logger::write("3D elements are of type '" + name +
                      "' (type = " + std::to_string(eleType3D) + ") ");

  // iterate over all volumes, get the 3D elements and create new 2D elements
  // for all faces
  std::vector<std::pair<int, int> > entities;
  gmsh::model::getEntities(entities, 3);
  for(std::size_t i = 0; i < entities.size(); i++) {
    int v = entities[i].second;
    std::vector<std::size_t> elementTags, nodeTags;
    gmsh::model::mesh::getElementsByType(eleType3D, elementTags, nodeTags, v);
    gmsh::logger::write("- " + std::to_string(elementTags.size()) +
                        " elements in volume " + std::to_string(v));

    // get the nodes on the triangular faces of the 3D elements
    std::vector<std::size_t> nodes;
    gmsh::model::mesh::getElementFaceNodes(eleType3D, 3, nodes, v);

    // create a new discrete entity of dimension 2
    int s = gmsh::model::addDiscreteEntity(2);

    // and add new 2D elements to it, for all faces
    int eleType2D = gmsh::model::mesh::getElementType("triangle", order);
    gmsh::model::mesh::addElementsByType(s, eleType2D, {}, nodes);

    // this will create two 2D elements for each face; to create unique elements
    // it would be useful to call getElementFaceNodes() with the extra `primary'
    // argument set to 'true' (to only get corner nodes even in the high-order
    // case, i.e. consider topological faces), then sort them and make them
    // unique.

    // this could be enriched with additional info: each topological face could
    // be associated with the tag of its parent element; in the sorting process
    // (eliminating duplicates) a second tag can be associated for internal
    // faces, allowing to keep track of neighbors
  }

  // gmsh::write("faces.msh");

  // iterate over all 2D elements and get integration information
  gmsh::model::mesh::getElementTypes(eleTypes, 2);
  int eleType2D = eleTypes[0];
  std::vector<double> uvw, q;
  gmsh::model::mesh::getIntegrationPoints(eleType2D, "Gauss3", uvw, q);
  std::vector<double> bf;
  int numComp, numOrientations;
  gmsh::model::mesh::getBasisFunctions(eleType2D, uvw, "Lagrange", numComp,
                                       bf, numOrientations);
  gmsh::model::getEntities(entities, 2);
  for(std::size_t i = 0; i < entities.size(); i++) {
    int s = entities[i].second;
    std::vector<std::size_t> elementTags, nodeTags;
    gmsh::model::mesh::getElementsByType(eleType2D, elementTags, nodeTags, s);
    gmsh::logger::write("- " + std::to_string(elementTags.size()) +
                        " elements on surface " + std::to_string(s));
    std::vector<double> jac, det, pts;
    gmsh::model::mesh::getJacobians(eleType2D, uvw, jac, det, pts, s);
  }

  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
