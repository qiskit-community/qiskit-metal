import gmsh
import sys

gmsh.initialize(sys.argv)

v0 = gmsh.model.occ.addSphere(0,0,0, 2)

# create wires in the parametric plane of the spherical surface [-pi,pi]x[-pi/2,pi/2]
c1 = gmsh.model.occ.addCircle(0,0,0, 0.4)
w1 = gmsh.model.occ.addWire([c1])

c2 = gmsh.model.occ.addCircle(0,0,0, 0.2)
w2 = gmsh.model.occ.addWire([c2])

s3 = gmsh.model.occ.addRectangle(0,0.5,0, 5,0.5)
gmsh.model.occ.synchronize()
b3 = gmsh.model.getBoundary([(2, s3)])
w3 = gmsh.model.occ.addWire([p[1] for p in b3])

# get spherical surface
s0 = gmsh.model.getBoundary([(3, v0)])[0][1]

# create 2 trimmed surfaces from the spherical surface, using the wires
gmsh.model.occ.addTrimmedSurface(s0, [w1, w2])
gmsh.model.occ.addTrimmedSurface(s0, [w3])

# remove the sphere
gmsh.model.occ.remove([(3, v0)], recursive=True)

gmsh.model.occ.synchronize()

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
