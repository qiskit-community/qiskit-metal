#include <gmsh.h>
#include <set>

int main(int argc, char **argv)
{
  gmsh::initialize();
  int s1 = gmsh::model::occ::addRectangle(0, 0, 0, 1, 1);
  int s2 = gmsh::model::occ::addRectangle(-0.5, 0, 0, 1, 1);
  gmsh::model::occ::rotate({{2, s2}}, 0, 0.5, 0, 1, 0, 0, M_PI/2);
  std::vector<std::pair<int, int> > out;
  std::vector<std::vector<std::pair<int, int> > > outmap;
  gmsh::model::occ::fragment({{2, s1}}, {{2, s2}}, out, outmap);
  gmsh::model::occ::synchronize();

  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();
}
