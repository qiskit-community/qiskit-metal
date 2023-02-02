# ------------------------------------------------------------------------------
#
#  Gmsh Python tutorial 6
#
#  Transfinite meshes
#
# ------------------------------------------------------------------------------

import gmsh
import math
import sys

gmsh.initialize()

gmsh.model.add("t6")

# Copied from `t1.py'...
lc = 1e-2
gmsh.model.geo.addPoint(0, 0, 0, lc, 1)
gmsh.model.geo.addPoint(.1, 0, 0, lc, 2)
gmsh.model.geo.addPoint(.1, .3, 0, lc, 3)
gmsh.model.geo.addPoint(0, .3, 0, lc, 4)
gmsh.model.geo.addLine(1, 2, 1)
gmsh.model.geo.addLine(3, 2, 2)
gmsh.model.geo.addLine(3, 4, 3)
gmsh.model.geo.addLine(4, 1, 4)
gmsh.model.geo.addCurveLoop([4, 1, -2, 3], 1)
gmsh.model.geo.addPlaneSurface([1], 1)

# Delete the surface and the left line, and replace the line with 3 new ones:
gmsh.model.geo.remove([(2, 1), (1, 4)])

p1 = gmsh.model.geo.addPoint(-0.05, 0.05, 0, lc)
p2 = gmsh.model.geo.addPoint(-0.05, 0.1, 0, lc)
l1 = gmsh.model.geo.addLine(1, p1)
l2 = gmsh.model.geo.addLine(p1, p2)
l3 = gmsh.model.geo.addLine(p2, 4)

# Create surface
gmsh.model.geo.addCurveLoop([2, -1, l1, l2, l3, -3], 2)
gmsh.model.geo.addPlaneSurface([-2], 1)

# The `setTransfiniteCurve()' meshing constraints explicitly specifies the
# location of the nodes on the curve. For example, the following command forces
# 20 uniformly placed nodes on curve 2 (including the nodes on the two end
# points):
gmsh.model.geo.mesh.setTransfiniteCurve(2, 20)

# Let's put 20 points total on combination of curves `l1', `l2' and `l3' (beware
# that the points `p1' and `p2' are shared by the curves, so we do not create 6
# + 6 + 10 = 22 nodes, but 20!)
gmsh.model.geo.mesh.setTransfiniteCurve(l1, 6)
gmsh.model.geo.mesh.setTransfiniteCurve(l2, 6)
gmsh.model.geo.mesh.setTransfiniteCurve(l3, 10)

# Finally, we put 30 nodes following a geometric progression on curve 1
# (reversed) and on curve 3: Put 30 points following a geometric progression
gmsh.model.geo.mesh.setTransfiniteCurve(1, 30, "Progression", -1.2)
gmsh.model.geo.mesh.setTransfiniteCurve(3, 30, "Progression", 1.2)

# The `setTransfiniteSurface()' meshing constraint uses a transfinite
# interpolation algorithm in the parametric plane of the surface to connect the
# nodes on the boundary using a structured grid. If the surface has more than 4
# corner points, the corners of the transfinite interpolation have to be
# specified by hand:
gmsh.model.geo.mesh.setTransfiniteSurface(1, "Left", [1, 2, 3, 4])

# To create quadrangles instead of triangles, one can use the `setRecombine'
# constraint:
gmsh.model.geo.mesh.setRecombine(2, 1)

# When the surface has only 3 or 4 points on its boundary the list of corners
# can be omitted in the `setTransfiniteSurface()' call:
gmsh.model.geo.addPoint(0.2, 0.2, 0, 1.0, 7)
gmsh.model.geo.addPoint(0.2, 0.1, 0, 1.0, 8)
gmsh.model.geo.addPoint(0, 0.3, 0, 1.0, 9)
gmsh.model.geo.addPoint(0.25, 0.2, 0, 1.0, 10)
gmsh.model.geo.addPoint(0.3, 0.1, 0, 1.0, 11)
gmsh.model.geo.addLine(8, 11, 10)
gmsh.model.geo.addLine(11, 10, 11)
gmsh.model.geo.addLine(10, 7, 12)
gmsh.model.geo.addLine(7, 8, 13)
gmsh.model.geo.addCurveLoop([13, 10, 11, 12], 14)
gmsh.model.geo.addPlaneSurface([14], 15)
for i in range(10, 14):
    gmsh.model.geo.mesh.setTransfiniteCurve(i, 10)
gmsh.model.geo.mesh.setTransfiniteSurface(15)

# The way triangles are generated can be controlled by specifying "Left",
# "Right" or "Alternate" in `setTransfiniteSurface()' command. Try e.g.
#
# gmsh.model.geo.mesh.setTransfiniteSurface(15, "Alternate")

gmsh.model.geo.synchronize()

# Finally we apply an elliptic smoother to the grid to have a more regular
# mesh:
gmsh.option.setNumber("Mesh.Smoothing", 100)

gmsh.model.mesh.generate(2)
gmsh.write("t6.msh")

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
