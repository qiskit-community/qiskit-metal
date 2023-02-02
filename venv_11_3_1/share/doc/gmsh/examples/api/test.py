import gmsh
import sys

gmsh.initialize(sys.argv)
print(gmsh.option.getNumber("Mesh.Algorithm"))

gmsh.open("square.msh")

gmsh.model.add("square")
gmsh.model.geo.addPoint(0, 0, 0, 0.1, 1)
gmsh.model.geo.addPoint(1, 0, 0, 0.1, 2)
gmsh.model.geo.addPoint(1, 1, 0, 0.1, 3)
gmsh.model.geo.addPoint(0, 1, 0, 0.1, 4)
gmsh.model.geo.addLine(1, 2, 1)
gmsh.model.geo.addLine(2, 3, 2)
gmsh.model.geo.addLine(3, 4, 3)
line4 = gmsh.model.geo.addLine(4, 1)
print("line4 received tag ", line4)
gmsh.model.geo.addCurveLoop([1, 2, 3, line4], 1)
gmsh.model.geo.addPlaneSurface([1], 6)
gmsh.model.geo.synchronize()

ptag = gmsh.model.addPhysicalGroup(1, [1, 2, 3, 4])
ent = gmsh.model.getEntitiesForPhysicalGroup(1, ptag)
print("new physical group ", ptag, ":", ent, type(ent))

gmsh.model.addPhysicalGroup(2, [6])

print(gmsh.option.getString("General.BuildOptions"))
print(gmsh.option.getNumber("Mesh.Algorithm"))
gmsh.option.setNumber("Mesh.Algorithm", 3.0)
print(gmsh.option.getNumber("Mesh.Algorithm"))
gmsh.model.mesh.generate(2)

gmsh.write("square.msh")

print("Entities")
entities = gmsh.model.getEntities()
for e in entities:
    print("entity ", e)
    types, tags, nodes = gmsh.model.mesh.getElements(e[0], e[1])
    for i in range(len(types)):
        print("type ", types[i])
        print("tags : ", list(tags[i]))
        print("nodes : ", list(nodes[i]))
    if e[0] == [2] and e[1] == 6:
        gmsh.model.mesh.addElements(e[0], e[1], types, [tags[0][:10]],
                                    [nodes[0][:30]])

gmsh.write("mesh_truncated.msh")
print("Nodes")
tags, coord, _ = gmsh.model.mesh.getNodes(2, 6)
print(tags)
print(coord)
gmsh.finalize()
