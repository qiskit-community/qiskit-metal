#include <gmsh.h>
#include <set>

int main(int argc, char **argv)
{
  gmsh::initialize();
  gmsh::model::occ::addRectangle(0, 0, 0, 1, 1, 1);
  gmsh::model::occ::synchronize();
  gmsh::model::mesh::setTransfiniteSurface(1);
  gmsh::option::setNumber("Mesh.MeshSizeMin", 1);
  gmsh::option::setNumber("Mesh.MeshSizeMax", 1);
  gmsh::model::mesh::generate();

  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
}
