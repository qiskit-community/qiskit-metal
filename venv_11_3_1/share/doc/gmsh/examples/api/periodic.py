import gmsh

gmsh.initialize()

gmsh.model.add("periodic")
R = 2
gmsh.model.occ.addBox(0, 0, 0, R, R, R)
gmsh.model.occ.synchronize()

ent = gmsh.model.getEntities(0)
gmsh.model.mesh.setSize(ent, 1)
gmsh.model.mesh.setSize([(0, 1)], 0.01)
gmsh.model.mesh.setPeriodic(2, [2], [1],
                            [1, 0, 0, R, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])

gmsh.model.mesh.generate(2)
#gmsh.model.mesh.setOrder(2)

masterTag, nodeTags, nodeMasterTags, tfo = gmsh.model.mesh.getPeriodicNodes(
    2, 2, includeHighOrderNodes=False)
print(masterTag, nodeTags, nodeMasterTags, tfo)

print(gmsh.model.mesh.getPeriodicKeys(2, "Lagrange", 2))

gmsh.write("periodic.msh")
gmsh.finalize()
