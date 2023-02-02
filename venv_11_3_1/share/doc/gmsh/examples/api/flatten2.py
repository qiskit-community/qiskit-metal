import gmsh
import sys

# script showing how the coordinates of the nodes of a mesh can be transformed,
# here by setting all the z coordinates to 0; this is less general, but much
# simpler, than the approach followed in `flatten.py'

if len(sys.argv) < 2:
    print("Usage: " + sys.argv[0] + " file.msh")
    exit(0)

gmsh.initialize()
gmsh.open(sys.argv[1])

gmsh.model.mesh.affineTransform([1, 0, 0, 0,
                                 0, 1, 0, 0,
                                 0, 0, 0, 0])

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()
#gmsh.write('flat.msh')

gmsh.finalize()
