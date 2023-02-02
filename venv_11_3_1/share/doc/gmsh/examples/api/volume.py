import gmsh
import sys

gmsh.initialize(sys.argv)

s = gmsh.model.occ.addRectangle(0, 0, 0, 3, 2)
gmsh.model.occ.synchronize()

m = gmsh.model.occ.getMass(2, s)
print("mass from occ = ", m)

p = gmsh.model.addPhysicalGroup(2, [s])
gmsh.model.mesh.generate(2)

gmsh.plugin.setNumber("MeshVolume", "Dimension", 2)
gmsh.plugin.setNumber("MeshVolume", "PhysicalGroup", p)
t = gmsh.plugin.run("MeshVolume")

_, _, data = gmsh.view.getListData(t)
print("volume from mesh = ", data[0][3])

gmsh.finalize()
