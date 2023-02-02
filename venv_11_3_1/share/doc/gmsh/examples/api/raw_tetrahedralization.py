import numpy as np
import gmsh
import sys

# number of points to tetrahedralize
N = 100

# visualize the mesh?
visu = ("-nopopup" not in sys.argv)

gmsh.initialize()

gmsh.option.setNumber('Mesh.Algorithm3D', 10) # new algo

points = np.random.standard_normal(3 * N)
tets = gmsh.model.mesh.tetrahedralize(points)

if visu:
    vol = gmsh.model.addDiscreteEntity(3)
    gmsh.model.mesh.addNodes(3, vol, range(1, N+1), points)
    gmsh.model.mesh.addElementsByType(vol, 4, [], tets)
    gmsh.fltk.run()

gmsh.finalize()
