import gmsh
gmsh.initialize()
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)  # save in old MSH format
N = 4
Rec2d = True  # tris or quads
Rec3d = True  # tets, prisms or hexas
p = gmsh.model.geo.addPoint(0, 0, 0)
l = gmsh.model.geo.extrude([(0, p)], 1, 0, 0, [N], [1])
s = gmsh.model.geo.extrude([l[1]], 0, 1, 0, [N], [1], recombine=Rec2d)
v = gmsh.model.geo.extrude([s[1]], 0, 0, 1, [N], [1], recombine=Rec3d)
gmsh.model.geo.synchronize()
gmsh.model.addPhysicalGroup(3, [v[1][1]])
gmsh.model.mesh.generate(3)
gmsh.write("mesh.msh")
gmsh.finalize()
