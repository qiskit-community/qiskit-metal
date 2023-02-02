#include <gmsh.h>
#include <math.h>

void create_mesh(std::size_t N, std::vector<double> &coords,
                 std::vector<std::size_t> &nodes,
                 std::vector<std::size_t> &tris)
{
  auto get_node_tag = [N](std::size_t i, std::size_t j) {
    return (N + 1) * i + j + 1;
  };
  std::size_t k = 0, l = 0;
  for(std::size_t i = 0; i < N + 1; i++) {
    for(std::size_t j = 0; j < N + 1; j++) {
      nodes[k] = get_node_tag(i, j);
      coords[3 * k] = (double)i / N;
      coords[3 * k + 1] = (double)j / N;
      coords[3 * k + 2] = 0.05 * sin(10 * (double)(i + j) / N);
      k++;
      if(i > 0 && j > 0) {
        tris[6 * l] = get_node_tag(i - 1, j - 1);
        tris[6 * l + 1] = get_node_tag(i, j - 1);
        tris[6 * l + 2] = get_node_tag(i - 1, j);
        tris[6 * l + 3] = get_node_tag(i, j - 1);
        tris[6 * l + 4] = get_node_tag(i, j);
        tris[6 * l + 5] = get_node_tag(i - 1, j);
        l++;
      }
    }
  }
}

int main()
{
  gmsh::initialize();

  int N = 2500;

  double tic = gmsh::logger::getWallTime();
  // x, y, z coordinates of all the nodes
  std::vector<double> coords((N + 1) * (N + 1) * 3);
  // tags of corresponding nodes
  std::vector<std::size_t> nodes((N + 1) * (N + 1));
  // connectivities (node tags) of triangle elements
  std::vector<std::size_t> tris(N * N * 2 * 3);

  create_mesh(N, coords, nodes, tris);

  double toc = gmsh::logger::getWallTime();
  printf("==> created nodes and connectivities in %g seconds\n", toc - tic);

  tic = gmsh::logger::getWallTime();
  int surf = gmsh::model::addDiscreteEntity(2);
  toc = gmsh::logger::getWallTime();
  printf("==> created surface in %g seconds\n", toc - tic);

  tic = gmsh::logger::getWallTime();
  gmsh::model::mesh::addNodes(2, 1, nodes, coords);
  toc = gmsh::logger::getWallTime();
  printf("==> imported nodes in %g seconds\n", toc - tic);

  tic = gmsh::logger::getWallTime();
  gmsh::model::mesh::addElementsByType(1, 2, {}, tris);
  toc = gmsh::logger::getWallTime();
  printf("==> imported elements in %g seconds\n", toc - tic);

  tic = gmsh::logger::getWallTime();
  gmsh::option::setNumber("Mesh.Binary", 1);
  gmsh::write("import_perf.msh");
  toc = gmsh::logger::getWallTime();
  printf("==> wrote to disk in %g seconds\n", toc - tic);

  tic = gmsh::logger::getWallTime();
  gmsh::merge("import_perf.msh");
  toc = gmsh::logger::getWallTime();
  printf("==> read from disk in %g seconds\n", toc - tic);

  //gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
