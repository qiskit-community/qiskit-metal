import gmsh
import sys

gmsh.initialize()

gmsh.model.occ.addCircle(0,0,0, 0.2)
gmsh.model.occ.addCircle(1,0,0, 0.2, zAxis=[0,0,1])
gmsh.model.occ.addCircle(2,0,0, 0.2, zAxis=[0,0,-1], xAxis=[1,0,0])
gmsh.model.occ.addCircle(3,0,0, 0.2, zAxis=[1,1,0], xAxis=[0,1,0])

gmsh.model.occ.addEllipse(0,-1,0, 0.2, 0.1)
gmsh.model.occ.addEllipse(1,-1,0, 0.2, 0.1, zAxis=[1,1,0], xAxis=[0,1,0])
gmsh.model.occ.addEllipse(2,-1,0, 0.2, 0.1, zAxis=[1,0,0], xAxis=[0,1,0])

gmsh.model.occ.addDisk(0,-2,0, 0.2, 0.1)
gmsh.model.occ.addDisk(1,-2,0, 0.2, 0.1, zAxis=[1,1,0], xAxis=[0,1,0])

gmsh.model.occ.addTorus(0,-3,0, 0.3, 0.1)
gmsh.model.occ.addTorus(1,-3,0, 0.3, 0.1, zAxis=[1,1,0])

gmsh.model.occ.addWedge(0,-4,0, 0.4, 0.2, 0.4)
gmsh.model.occ.addWedge(1,-4,0, 0.4, 0.2, 0.4, zAxis=[0.2,0,1])

gmsh.model.occ.synchronize()

gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 10)

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()
