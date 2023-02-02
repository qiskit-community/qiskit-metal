import gmsh
import sys

gmsh.initialize()
gmsh.model.occ.addBox(0,0,0,1,1,1)
gmsh.model.occ.addBox(1,0,0,1,1,1)
gmsh.model.occ.removeAllDuplicates()
gmsh.model.occ.synchronize()

gmsh.model.mesh.generate(3)

# Mesh.MeshOnlyVisible can be used to selectively mesh, or in this case set the
# order, on parts of a model

gmsh.option.setNumber('Mesh.MeshOnlyVisible', 1)
gmsh.model.setVisibility([(3,2)], 0, recursive=True)

gmsh.model.mesh.setOrder(2) # only on volume 1
gmsh.model.setVisibility([(3,2)], 1, recursive=True)

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()
