// -----------------------------------------------------------------------------
//
//  Gmsh C++ extended tutorial 7
//
//  Additional mesh data: internal edges and faces
//
// -----------------------------------------------------------------------------

#include <iostream>
#include <set>
#include <map>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);
  gmsh::model::add("x7");

  // Meshes are fully described in Gmsh by nodes and elements, both associated
  // to model entities. The API can be used to generate and handle other mesh
  // entities, i.e. mesh edges and faces, which are not stored by default.

  // Let's create a simple model and mesh it:
  gmsh::model::occ::addBox(0, 0, 0, 1, 1, 1);
  gmsh::model::occ::synchronize();
  gmsh::option::setNumber("Mesh.MeshSizeMin", 2.);
  gmsh::model::mesh::generate(3);

  // Like elements, mesh edges and faces are described by (an ordered list of)
  // their nodes. Let us retrieve the edges and the (triangular) faces of all
  // the first order tetrahedra in the mesh:
  int elementType = gmsh::model::mesh::getElementType("tetrahedron", 1);
  std::vector<std::size_t> edgeNodes, faceNodes;
  gmsh::model::mesh::getElementEdgeNodes(elementType, edgeNodes);
  gmsh::model::mesh::getElementFaceNodes(elementType, 3, faceNodes);

  // Edges and faces are returned for each element as a list of nodes
  // corresponding to the canonical orientation of the edges and faces for a
  // given element type.

  // Gmsh can also identify unique edges and faces (a single edge or face
  // whatever the ordering of their nodes) and assign them a unique tag. This
  // identification can be done internally by Gmsh (e.g. when generating keys
  // for basis functions), or requested explicitly as follows:
  gmsh::model::mesh::createEdges();
  gmsh::model::mesh::createFaces();

  // Edge and face tags can then be retrieved by providing their nodes:
  std::vector<std::size_t> edgeTags, faceTags;
  std::vector<int> edgeOrientations, faceOrientations;
  gmsh::model::mesh::getEdges(edgeNodes, edgeTags, edgeOrientations);
  gmsh::model::mesh::getFaces(3, faceNodes, faceTags, faceOrientations);

  // Since element edge and face nodes are returned in the same order as the
  // elements, one can easily keep track of which element(s) each edge or face
  // is connected to:
  std::vector<std::size_t> elementTags, elementNodeTags;
  gmsh::model::mesh::getElementsByType(elementType, elementTags, elementNodeTags);
  std::map<std::size_t, std::vector<std::size_t>> edges2Elements, faces2Elements;
  for(std::size_t i = 0; i < edgeTags.size(); i++) // 6 edges per tetrahedron
    edges2Elements[edgeTags[i]].push_back(elementTags[i / 6]);
  for(std::size_t i = 0; i < faceTags.size(); i++) // 4 faces per tetrahedron
    faces2Elements[faceTags[i]].push_back(elementTags[i / 4]);

  // New unique lower dimensional elements can also be easily created given the
  // edge or face nodes. This is especially useful for numerical methods that
  // require integrating or interpolating on internal edges or faces (like
  // e.g. Discontinuous Galerkin techniques), since creating elements for the
  // internal entities will make this additional mesh data readily available
  // (see `x6.cpp'). For example, we can create a new discrete surface...
  int s = gmsh::model::addDiscreteEntity(2);

  // ... and fill it with unique triangles corresponding to the faces of the
  // tetrahedra:
  std::set<std::size_t> uniqueFaceTags;
  std::vector<std::size_t> tagsForTriangles, faceNodesForTriangles;
  std::size_t maxElementTag;
  gmsh::model::mesh::getMaxElementTag(maxElementTag);
  for(std::size_t i = 0; i < faceTags.size(); i++) {
    if(uniqueFaceTags.find(faceTags[i]) == uniqueFaceTags.end()) {
      uniqueFaceTags.insert(faceTags[i]);
      tagsForTriangles.push_back(faceTags[i] + maxElementTag);
      faceNodesForTriangles.push_back(faceNodes[3 * i]);
      faceNodesForTriangles.push_back(faceNodes[3 * i + 1]);
      faceNodesForTriangles.push_back(faceNodes[3 * i + 2]);
    }
  }
  int elementType2D = gmsh::model::mesh::getElementType("triangle", 1);
  gmsh::model::mesh::addElementsByType(s, elementType2D, tagsForTriangles,
                                       faceNodesForTriangles);

  // Since the tags for the triangles have been created based on the face tags,
  // the information about neighboring elements can also be readily created,
  // useful e.g. in Finite Volume or Discontinuous Galerkin techniques:
  for(auto t : tagsForTriangles) {
    std::cout << "triangle " << t << " is connected to tetrahedra ";
    for(auto tt : faces2Elements[t - maxElementTag]) std::cout << tt << " ";
    std::cout << "\n";
  }

  // If all you need is the list of all edges or faces in terms of their nodes, you
  // can also directly call:
  gmsh::model::mesh::getAllEdges(edgeTags, edgeNodes);
  gmsh::model::mesh::getAllFaces(3, faceTags, faceNodes);

  // Launch the GUI to see the results:
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
