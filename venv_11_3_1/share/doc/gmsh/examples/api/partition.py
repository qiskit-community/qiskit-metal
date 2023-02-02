import gmsh
import sys

write_file = False
write_one_file_per_partition = False
partition_using_metis = False

gmsh.initialize()

# create a simple geometry and mesh it
gmsh.model.add("test")
gmsh.model.occ.addRectangle(0, 0, 0, 1, 1)
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(2)

# partition the mesh using Metis, or using the SimplePartition plugin (to create
# simple chessboard-like partitions). This will create new ("partitioned")
# entities in the model, that will behave exactly like other model entities. In
# particular, the full boundary representation is constructed provided that
# Mesh.PartitionCreateTopology == 1. The only difference is that partitioned
# entities have a "parent", which allows to link the partitioned entity with the
# entity it is a subset of. There are other options to govern how physical
# groups are treated (Mesh.PartitionCreatePhysicals), and if ghost cells should
# be created (Mesh.PartitionCreateGhostCells).
if partition_using_metis:
    gmsh.model.mesh.partition(3)
else:
    gmsh.plugin.setNumber("SimplePartition", "NumSlicesX", 3.)
    gmsh.plugin.run("SimplePartition")

# write the partitioned mesh to disk?
if write_file:
    # create one file per partition?
    if write_one_file_per_partition:
        gmsh.option.setNumber("Mesh.PartitionSplitMeshFiles", 1)
    gmsh.write("partition.msh")

# iterate over partitioned entities and print some info
entities = gmsh.model.getEntities()
for e in entities:
    partitions = gmsh.model.getPartitions(e[0], e[1])
    if len(partitions):
        print("Entity " + str(e) + " of type " +
              gmsh.model.getType(e[0], e[1]))
        print(" - Partition(s): " + str(partitions))
        print(" - Parent: " + str(gmsh.model.getParent(e[0], e[1])))
        print(" - Boundary: " + str(gmsh.model.getBoundary([e])))

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
