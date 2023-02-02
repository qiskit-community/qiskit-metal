#include <gmsh.h>
#include <iostream>
#include <set>

int main(int argc, char **argv)
{
  bool write_file = false;
  bool write_one_file_per_partition = false;
  bool partition_using_metis = false;

  gmsh::initialize();

  // create a simple geometry and mesh it
  gmsh::model::add("test");
  gmsh::model::occ::addRectangle(0, 0, 0, 1, 1);
  gmsh::model::occ::synchronize();
  gmsh::model::mesh::generate(2);

  // partition the mesh using Metis, or using the SimplePartition plugin (to
  // create simple chessboard-like partitions). This will create new
  // ("partitioned") entities in the model, that will behave exactly like other
  // model entities. In particular, the full boundary representation is
  // constructed provided that Mesh.PartitionCreateTopology == 1. The only
  // difference is that partitioned entities have a "parent", which allows to
  // link the partitioned entity with the entity it is a subset of. There are
  // other options to govern how physical groups are treated
  // (Mesh.PartitionCreatePhysicals), and if ghost cells should be created
  // (Mesh.PartitionCreateGhostCells).
  if(partition_using_metis) { gmsh::model::mesh::partition(3); }
  else {
    gmsh::plugin::setNumber("SimplePartition", "NumSlicesX", 3.);
    gmsh::plugin::run("SimplePartition");
  }

  // write the partitioned mesh to disk?
  if(write_file) {
    // create one file per partition?
    if(write_one_file_per_partition) {
      gmsh::option::setNumber("Mesh.PartitionSplitMeshFiles", 1);
    }
    gmsh::write("partition.msh");
  }

  // iterate over partitioned entities and print some info
  std::vector<std::pair<int, int> > entities;
  gmsh::model::getEntities(entities);

  for(std::vector<std::pair<int, int> >::iterator it = entities.begin();
      it != entities.end(); it++) {
    std::vector<int> partitions;
    gmsh::model::getPartitions(it->first, it->second, partitions);
    if(partitions.size()) {
      std::string type;
      gmsh::model::getType(it->first, it->second, type);
      std::cout << "Entity (" << it->first << "," << it->second << ") "
                << "of type " << type << "\n";
      std::cout << " - Partition(s):";
      for(std::size_t i = 0; i < partitions.size(); i++)
        std::cout << " " << partitions[i];
      std::cout << "\n";
      int pdim, ptag;
      gmsh::model::getParent(it->first, it->second, pdim, ptag);
      std::cout << " - Parent: (" << pdim << "," << ptag << ")\n";
      std::vector<std::pair<int, int> > bnd;
      gmsh::model::getBoundary({*it}, bnd);
      std::cout << " - Boundary:";
      for(std::size_t i = 0; i < bnd.size(); i++)
        std::cout << " (" << bnd[i].first << "," << bnd[i].second << ")";
      std::cout << "\n";
    }
  }

  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();

  return 0;
}
