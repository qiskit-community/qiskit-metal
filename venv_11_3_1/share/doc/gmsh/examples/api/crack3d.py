import gmsh
import sys

gmsh.initialize(sys.argv)

# create 2 adjacent boxes + a smaller surface on the interface
v1 = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
v2 = gmsh.model.occ.addBox(0, 0, -1, 1, 1, 1)
s1 = gmsh.model.occ.addRectangle(0.25, 0.25, 0, 0.5, 0.5)

# fragment the model to make the geometry conformal
out, out_map = gmsh.model.occ.fragment([(2, s1)], [(3, v1), (3, v2)])

# out_map contains the corresondence between the input and output entities after
# fragmentation: out_map[0] will thus contain the entities (as (dim, tag) pairs)
# replacing the surface s1

# synchronize with the topological model
gmsh.model.occ.synchronize()

# define a physical group on the small surface (the "Crack" uses physical groups
# as input)
phys = gmsh.model.addPhysicalGroup(2, [out_map[0][0][1]])

# generate conformal mesh
gmsh.model.mesh.generate(3)

# "crack" the mesh by duplicating the elements and nodes on the small surface
gmsh.plugin.setNumber("Crack", "Dimension", 2)
gmsh.plugin.setNumber("Crack", "PhysicalGroup", phys)
gmsh.plugin.setNumber("Crack", "DebugView", 1)
gmsh.plugin.run("Crack")

# save all the elements in the mesh (even those that do not belong to any
# physical group):
gmsh.option.setNumber("Mesh.SaveAll", 1)
gmsh.write("crack.msh")

# show the result
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
