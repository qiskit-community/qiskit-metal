import gmsh
import sys

gmsh.initialize()

# add a circle
c = gmsh.model.occ.addCircle(0, 0, 0, 1)
gmsh.model.occ.synchronize()

# find closet point to (1.3, 1.3) by orthogonal projection on the curve c
p, t = gmsh.model.getClosestPoint(1, c, [1.3, 1.3, 0])

# add a point on the projection
pp = gmsh.model.occ.addPoint(p[0], p[1], p[2])

# fragment the curve with the new point
gmsh.model.occ.fragment([(0, pp)], [(1, c)])

gmsh.model.occ.synchronize()

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
