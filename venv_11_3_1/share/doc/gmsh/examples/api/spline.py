import gmsh
import math
import sys

gmsh.initialize()

gmsh.model.add("spline")

for i in range(1, 11):
    gmsh.model.occ.addPoint(i, math.sin(i / 9. * 2. * math.pi), 0, 0.1, i)

gmsh.model.occ.addSpline(range(1, 11), 1)
gmsh.model.occ.addBSpline(range(1, 11), 2)
gmsh.model.occ.addBezier(range(1, 11), 3)

gmsh.model.occ.addPoint(0.2, -1.6, 0, 0.1, 101)
gmsh.model.occ.addPoint(1.2, -1.6, 0, 0.1, 102)
gmsh.model.occ.addPoint(1.2, -1.1, 0, 0.1, 103)
gmsh.model.occ.addPoint(0.3, -1.1, 0, 0.1, 104)
gmsh.model.occ.addPoint(0.7, -1, 0, 0.1, 105)

# periodic bspline through the control points
gmsh.model.occ.addSpline([103, 102, 101, 104, 105, 103], 100)

# periodic bspline from given control points and default parameters - will
# create a new vertex
gmsh.model.occ.addBSpline([103, 102, 101, 104, 105, 103], 101)

# general bspline with explicit degree, knots and multiplicities
gmsh.model.occ.addPoint(0, -2, 0, 0.1, 201)
gmsh.model.occ.addPoint(1, -2, 0, 0.1, 202)
gmsh.model.occ.addPoint(1, -3, 0, 0.1, 203)
gmsh.model.occ.addPoint(0, -3, 0, 0.1, 204)
gmsh.model.occ.addBSpline([201, 202, 203, 204], 200, 2, [], [0, 0.5, 1],
                          [3, 1, 3])

gmsh.model.occ.synchronize()
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()
gmsh.finalize()
