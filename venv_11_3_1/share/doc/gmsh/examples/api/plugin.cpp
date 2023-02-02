#include <iostream>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize();

  // Copied from discrete.cpp...
  gmsh::model::add("test");
  gmsh::model::addDiscreteEntity(2, 1);
  gmsh::model::mesh::addNodes(2, 1, {1, 2, 3, 4},
                              {0., 0., 0., 1., 0., 0., 1., 1., 0., 0., 1., 0.});
  gmsh::model::mesh::addElements(2, 1, {2}, {{1, 2}}, {{1, 2, 3, 1, 3, 4}});
  // ... end of copy

  // create a view with some data
  int t = gmsh::view::add("some data");
  gmsh::view::addModelData(t, 0, "test", "NodeData", {1, 2, 3, 4},
                           {{1.}, {10.}, {20.}, {1.}});

  // test getting data back
  std::string dataType;
  std::vector<std::size_t> tags;
  std::vector<std::vector<double> > data;
  double time;
  int numComp;
  gmsh::view::getModelData(t, 0, dataType, tags, data, time, numComp);
  std::cout << dataType;
  for(unsigned int i = 0; i < tags.size(); i++) std::cout << " " << tags[i];
  std::cout << std::endl;

  // compute the iso-curve at value 11
  gmsh::plugin::setNumber("Isosurface", "Value", 11.);
  gmsh::plugin::run("Isosurface");

  // delete the source view
  gmsh::view::remove(t);

  // check how many views the plugin created (a priori, a single list-based one)
  std::vector<int> viewTags;
  gmsh::view::getTags(viewTags);
  if(viewTags.size() == 1) {
    gmsh::view::write(viewTags[0], "iso.msh");
    // test getting data back
    std::vector<std::string> dataTypes;
    std::vector<int> numElements;
    gmsh::view::getListData(viewTags[0], dataTypes, numElements, data);
    for(unsigned int i = 0; i < dataTypes.size(); i++)
      std::cout << dataTypes[i] << " ";
    for(unsigned int i = 0; i < numElements.size(); i++)
      std::cout << numElements[i] << " ";
    std::cout << std::endl;
  }

  gmsh::finalize();
  return 0;
}
