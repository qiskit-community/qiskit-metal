import gmsh

gmsh.initialize()

# load step file
gmsh.open('as1-tu-203.stp')

# get all model entities
ent = gmsh.model.getEntities()

gmsh.model.occ.healShapes()

gmsh.model.occ.synchronize()

gmsh.finalize()
