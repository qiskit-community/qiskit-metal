#include <iostream>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  // create a simple cartesian grid (you can make it finer e.g. by passing
  // "-clscale 0.01" on the command line)
  gmsh::model::add("square");
  gmsh::model::occ::addRectangle(0, 0, 0, 1, 1, 100);
  gmsh::model::occ::synchronize();
  gmsh::model::mesh::setTransfiniteSurface(100);
  gmsh::model::mesh::generate(2);

  // create a post-processing dataset
  gmsh::plugin::setNumber("NewView", "Value", 1.234);
  int t = gmsh::plugin::run("NewView");

  // retrieve the dataset as a vector of vectors (one per tag)
  std::string type;
  std::vector<std::size_t> tags;
  std::vector<std::vector<double> > data;
  double time;
  int numComp;
  std::cout << "before get" << std::endl;
  gmsh::view::getModelData(t, 0, type, tags, data, time, numComp);
  std::cout << "after get" << std::endl;

  // retrieve the dataset as a single vector
  std::vector<double> data2;
  std::cout << "before getHomogeneous" << std::endl;
  gmsh::view::getHomogeneousModelData(t, 0, type, tags, data2, time, numComp);
  std::cout << "after getHomogeneous" << std::endl;

  gmsh::finalize();
  return 0;
}
