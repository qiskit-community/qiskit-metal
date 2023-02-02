# ------------------------------------------------------------------------------
#
#  Gmsh Python tutorial 19
#
#  Thrusections, fillets, pipes, mesh size from curvature
#
# ------------------------------------------------------------------------------

# The OpenCASCADE geometry kernel supports several useful features for solid
# modelling.

import gmsh
import math
import os
import sys

gmsh.initialize()

gmsh.model.add("t19")

# Volumes can be constructed from (closed) curve loops thanks to the
# `addThruSections()' function
gmsh.model.occ.addCircle(0, 0, 0, 0.5, 1)
gmsh.model.occ.addCurveLoop([1], 1)
gmsh.model.occ.addCircle(0.1, 0.05, 1, 0.1, 2)
gmsh.model.occ.addCurveLoop([2], 2)
gmsh.model.occ.addCircle(-0.1, -0.1, 2, 0.3, 3)
gmsh.model.occ.addCurveLoop([3], 3)
gmsh.model.occ.addThruSections([1, 2, 3], 1)
gmsh.model.occ.synchronize()

# We can also force the creation of ruled surfaces:
gmsh.model.occ.addCircle(2 + 0, 0, 0, 0.5, 11)
gmsh.model.occ.addCurveLoop([11], 11)
gmsh.model.occ.addCircle(2 + 0.1, 0.05, 1, 0.1, 12)
gmsh.model.occ.addCurveLoop([12], 12)
gmsh.model.occ.addCircle(2 - 0.1, -0.1, 2, 0.3, 13)
gmsh.model.occ.addCurveLoop([13], 13)
gmsh.model.occ.addThruSections([11, 12, 13], 11, True, True)
gmsh.model.occ.synchronize()

# We copy the first volume, and fillet all its edges:
out = gmsh.model.occ.copy([(3, 1)])
gmsh.model.occ.translate(out, 4, 0, 0)
gmsh.model.occ.synchronize()
e = gmsh.model.getBoundary(gmsh.model.getBoundary(out), False)
gmsh.model.occ.fillet([out[0][1]], [abs(i[1]) for i in e], [0.1])
gmsh.model.occ.synchronize()

# OpenCASCADE also allows general extrusions along a smooth path. Let's first
# define a spline curve:
nturns = 1.
npts = 20
r = 1.
h = 1. * nturns
p = []
for i in range(0, npts):
    theta = i * 2 * math.pi * nturns / npts
    gmsh.model.occ.addPoint(r * math.cos(theta), r * math.sin(theta),
                            i * h / npts, 1, 1000 + i)
    p.append(1000 + i)
gmsh.model.occ.addSpline(p, 1000)

# A wire is like a curve loop, but open:
gmsh.model.occ.addWire([1000], 1000)

# We define the shape we would like to extrude along the spline (a disk):
gmsh.model.occ.addDisk(1, 0, 0, 0.2, 0.2, 1000)
gmsh.model.occ.rotate([(2, 1000)], 0, 0, 0, 1, 0, 0, math.pi / 2)

# We extrude the disk along the spline to create a pipe (other sweeping types
# can be specified; try e.g. 'Frenet' instead of 'DiscreteTrihedron'):
gmsh.model.occ.addPipe([(2, 1000)], 1000, 'DiscreteTrihedron')

# We delete the source surface, and increase the number of sub-edges for a
# nicer display of the geometry:
gmsh.model.occ.remove([(2, 1000)])
gmsh.option.setNumber("Geometry.NumSubEdges", 1000)

gmsh.model.occ.synchronize()

# We can activate the calculation of mesh element sizes based on curvature
# (here with a target of 20 elements per 2*Pi radians):
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 20)

# We can constraint the min and max element sizes to stay within reasonnable
# values (see `t10.py' for more details):
gmsh.option.setNumber("Mesh.MeshSizeMin", 0.001)
gmsh.option.setNumber("Mesh.MeshSizeMax", 0.3)

gmsh.model.mesh.generate(3)
gmsh.write("t19.msh")

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
