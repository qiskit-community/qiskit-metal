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

  // Create a new post-processing view
  int t = gmsh::view::add("some data");

  // add 10 steps of model-based data, on the nodes of the mesh
  for(int step = 0; step < 10; step++)
    gmsh::view::addModelData(
      t, step, "test", "NodeData", {1, 2, 3, 4}, // tags of nodes
      {{10.}, {10.}, {12. + step}, {13. + step}}); // data, per node

  gmsh::view::write(t, "data.msh");

  gmsh::finalize();
  return 0;
}
