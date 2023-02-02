#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize();

  std::vector<double> tri1 = {0., 1., 1., 0., 0., 1., 0., 0., 0.};
  std::vector<double> tri2 = {0., 1., 0., 0., 1., 1., 0., 0., 0.};

  for(int step = 0; step < 10; step++) {
    tri1.push_back(10.);
    tri1.push_back(10.);
    tri1.push_back(12. + step);
    tri2.push_back(10.);
    tri2.push_back(12. + step);
    tri2.push_back(13. + step);
  }

  int t = gmsh::view::add("some data");
  std::vector<double> data;
  data.insert(data.end(), tri1.begin(), tri1.end());
  data.insert(data.end(), tri2.begin(), tri2.end());

  gmsh::view::addListData(t, "ST", 2, data);

  gmsh::view::write(t, "data.pos");

  gmsh::finalize();
  return 0;
}
