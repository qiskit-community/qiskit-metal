// -----------------------------------------------------------------------------
//
//  Gmsh C++ tutorial 21
//
//  Mesh partitioning
//
// -----------------------------------------------------------------------------

#include <set>
#include <cmath>
#include <cstdlib>
#include <algorithm>
#include <iostream>
#include <gmsh.h>

// Gmsh can partition meshes using different algorithms, e.g. the graph
// partitioner Metis or the `SimplePartition' plugin. For all the partitioning
// algorithms, the relationship between mesh elements and mesh partitions is
// encoded through the creation of new (discrete) elementary entities, called
// "partition entities".
//
// Partition entities behave exactly like other discrete elementary entities;
// the only difference is that they keep track of both a mesh partition index
// and their parent elementary entity.
//
// The major advantage of this approach is that it allows to maintain a full
// boundary representation of the partition entities, which Gmsh creates
// automatically if `Mesh.PartitionCreateTopology' is set.

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  gmsh::model::add("t21");

  // Let us start by creating a simple geometry with two adjacent squares
  // sharing an edge:
  gmsh::model::add("t21");
  gmsh::model::occ::addRectangle(0, 0, 0, 1, 1, 1);
  gmsh::model::occ::addRectangle(1, 0, 0, 1, 1, 2);
  std::vector<std::pair<int, int> > ov;
  std::vector<std::vector<std::pair<int, int> > > ovv;
  gmsh::model::occ::fragment({{2, 1}}, {{2, 2}}, ov, ovv);
  gmsh::model::occ::synchronize();
  std::vector<std::pair<int, int> > tmp;
  gmsh::model::getEntities(tmp, 0);
  gmsh::model::mesh::setSize(tmp, 0.05);

  // We create one physical group for each square, and we mesh the resulting
  // geometry:
  gmsh::model::addPhysicalGroup(2, {1}, 100, "Left");
  gmsh::model::addPhysicalGroup(2, {2}, 200, "Right");
  gmsh::model::mesh::generate(2);

  // We now define several ONELAB parameters to fine-tune how the mesh will be
  // partitioned:
  gmsh::onelab::set(R"( [
  {
    "type":"number",
    "name":"Parameters/0Mesh partitioner",
    "values":[0],
    "choices":[0, 1],
    "valueLabels":{"Metis":0, "SimplePartition":1}
  },
  {
    "type":"number",
    "name":"Parameters/1Number of partitions",
    "values":[3],
    "min":1,
    "max":256,
    "step":1
  },
  {
    "type":"number",
    "name":"Parameters/2Create partition topology (BRep)?",
    "values":[1],
    "choices":[0, 1]
  },
  {
    "type":"number",
    "name":"Parameters/3Create ghost cells?",
    "values":[0],
    "choices":[0, 1]
  },
  {
    "type":"number",
    "name":"Parameters/3Create new physical groups?",
    "values":[0],
    "choices":[0, 1]
  },
  {
    "type":"number",
    "name":"Parameters/3Write file to disk?",
    "values":[1],
    "choices":[0, 1]
  },
  {
    "type":"number",
    "name":"Parameters/4Write one file per partition?",
    "values":[0],
    "choices":[0, 1]
  }
  ] )");

  auto partitionMesh = []()
  {
    // Number of partitions
    std::vector<double> n;
    gmsh::onelab::getNumber("Parameters/1Number of partitions", n);
    int N = static_cast<int>(n[0]);

    // Should we create the boundary representation of the partition entities?
    gmsh::onelab::getNumber("Parameters/2Create partition topology (BRep)?", n);
    gmsh::option::setNumber("Mesh.PartitionCreateTopology", n[0]);

    // Should we create ghost cells?
    gmsh::onelab::getNumber("Parameters/3Create ghost cells?", n);
    gmsh::option::setNumber("Mesh.PartitionCreateGhostCells", n[0]);

    // Should we automatically create new physical groups on the partition
    // entities?
    gmsh::onelab::getNumber("Parameters/3Create new physical groups?", n);
    gmsh::option::setNumber("Mesh.PartitionCreatePhysicals", n[0]);

    // Should we keep backward compatibility with pre-Gmsh 4, e.g. to save the
    // mesh in MSH2 format?
    gmsh::option::setNumber("Mesh.PartitionOldStyleMsh2", 0);

    // Should we save one mesh file per partition?
    gmsh::onelab::getNumber("Parameters/4Write one file per partition?", n);
    gmsh::option::setNumber("Mesh.PartitionSplitMeshFiles", n[0]);

    gmsh::onelab::getNumber("Parameters/0Mesh partitioner", n);
    if(n[0] == 0) {
      // Use Metis to create N partitions
      gmsh::model::mesh::partition(N);
      // Several options can be set to control Metis: `Mesh.MetisAlgorithm' (1:
      // Recursive, 2: K-way), `Mesh.MetisObjective' (1: min. edge-cut, 2:
      // min. communication volume), `Mesh.PartitionTriWeight' (weight of
      // triangles), `Mesh.PartitionQuadWeight' (weight of quads), ...
    }
    else {
      // Use the `SimplePartition' plugin to create chessboard-like partitions
      gmsh::plugin::setNumber("SimplePartition", "NumSlicesX", N);
      gmsh::plugin::setNumber("SimplePartition", "NumSlicesY", 1);
      gmsh::plugin::setNumber("SimplePartition", "NumSlicesZ", 1);
      gmsh::plugin::run("SimplePartition");
    }

    // Save mesh file (or files, if `Mesh.PartitionSplitMeshFiles' is set):
    gmsh::onelab::getNumber("Parameters/3Write file to disk?", n);
    if(n[0]) gmsh::write("t21.msh");

    // Iterate over partitioned entities and print some info (see the first
    // extended tutorial `x1.cpp' for additional information):
    std::vector<std::pair<int, int> > entities;
    gmsh::model::getEntities(entities);

    for(auto e : entities) {
      std::vector<int> partitions;
      gmsh::model::getPartitions(e.first, e.second, partitions);
      if(partitions.size()) {
        std::string type;
        gmsh::model::getType(e.first, e.second, type);
        std::cout << "Entity (" << e.first << "," << e.second << ") "
                  << "of type " << type << "\n";
        std::cout << " - Partition(s):";
        for(auto p : partitions) std::cout << " " << p;
        std::cout << "\n";
        int pdim, ptag;
        gmsh::model::getParent(e.first, e.second, pdim, ptag);
        std::cout << " - Parent: (" << pdim << "," << ptag << ")\n";
        std::vector<std::pair<int, int> > bnd;
        gmsh::model::getBoundary({e}, bnd);
        std::cout << " - Boundary:";
        for(auto b : bnd) std::cout << " (" << b.first << "," << b.second << ")";
        std::cout << "\n";
      }
    }
  };

  partitionMesh();

  // Launch the GUI and handle the "check" event to re-partition the mesh
  // according to the choices made in the GUI
  auto checkForEvent = [=]() -> bool {
    std::vector<std::string> action;
    gmsh::onelab::getString("ONELAB/Action", action);
    if(action.size() && action[0] == "check") {
      gmsh::onelab::setString("ONELAB/Action", {""});
      partitionMesh();
      gmsh::graphics::draw();
    }
    return true;
  };

  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) {
    gmsh::fltk::initialize();
    while(gmsh::fltk::isAvailable() && checkForEvent())
      gmsh::fltk::wait();
  }

  gmsh::finalize();
  return 0;
}
