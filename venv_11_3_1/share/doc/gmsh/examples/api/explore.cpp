#include <iostream>
#include <gmsh.h>

int main(int argc, char **argv)
{
  if(argc < 2) {
    std::cout << "Usage: " << argv[0] << " file.msh" << std::endl;
    return 0;
  }

  gmsh::initialize();

  gmsh::open(argv[1]);

  // get all elementary entities in the model
  std::vector<std::pair<int, int> > entities;
  gmsh::model::getEntities(entities);

  for(unsigned int i = 0; i < entities.size(); i++) {
    // get the mesh nodes for each elementary entity
    std::vector<std::size_t> nodeTags;
    std::vector<double> nodeCoords, nodeParams;
    int dim = entities[i].first, tag = entities[i].second;
    gmsh::model::mesh::getNodes(nodeTags, nodeCoords, nodeParams, dim, tag);

    // get the mesh elements for each elementary entity
    std::vector<int> elemTypes;
    std::vector<std::vector<std::size_t> > elemTags, elemNodeTags;
    gmsh::model::mesh::getElements(elemTypes, elemTags, elemNodeTags, dim, tag);

    // report some statistics
    int numElem = 0;
    for(unsigned int j = 0; j < elemTags.size(); j++)
      numElem += elemTags[j].size();
    std::string type;
    gmsh::model::getType(dim, tag, type);
    std::cout << nodeTags.size() << " mesh nodes and " << numElem
              << " mesh elements on entity (" << dim << "," << tag
              << ") of type " << type << "\n";
    std::vector<int> partitions;
    gmsh::model::getPartitions(dim, tag, partitions);
    if(partitions.size()) {
      std::cout << " - Partition tag(s):";
      for(unsigned int j = 0; j < partitions.size(); j++)
        std::cout << " " << partitions[j];
      int parentDim, parentTag;
      gmsh::model::getParent(dim, tag, parentDim, parentTag);
      std::cout << " - parent entity (" << parentDim << "," << parentTag
                << ")\n";
    }
    for(unsigned int j = 0; j < elemTypes.size(); j++) {
      std::string name;
      int d, order, numv, numpv;
      std::vector<double> param;
      gmsh::model::mesh::getElementProperties(elemTypes[j], name, d, order,
                                              numv, param, numpv);
      std::cout << " - Element type: " << name << ", order " << order << "\n";
      std::cout << "   with " << numv << " nodes in param coord: (";
      for(unsigned int k = 0; k < param.size(); k++)
        std::cout << param[k] << " ";
      std::cout << ")\n";
    }
  }

  gmsh::finalize();
  return 0;
}
