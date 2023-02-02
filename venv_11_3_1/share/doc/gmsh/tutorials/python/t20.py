# ------------------------------------------------------------------------------
#
#  Gmsh Python tutorial 20
#
#  STEP import and manipulation, geometry partitioning
#
# ------------------------------------------------------------------------------

# The OpenCASCADE CAD kernel allows to import STEP files and to modify them. In
# this tutorial we will load a STEP geometry and partition it into slices.

import gmsh
import math
import os
import sys

gmsh.initialize()

gmsh.model.add("t20")

# Load a STEP file (using `importShapes' instead of `merge' allows to directly
# retrieve the tags of the highest dimensional imported entities):
path = os.path.dirname(os.path.abspath(__file__))
v = gmsh.model.occ.importShapes(os.path.join(path, os.pardir, 't20_data.step'))

# If we had specified
#
# gmsh.option.setString('Geometry.OCCTargetUnit', 'M')
#
# before merging the STEP file, OpenCASCADE would have converted the units to
# meters (instead of the default, which is millimeters).

# Get the bounding box of the volume:
xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.occ.getBoundingBox(
    v[0][0], v[0][1])

# We want to slice the model into N slices, and either keep the volume slices
# or just the surfaces obtained by the cutting:

N = 5  # Number of slices
dir = 'X' # Direction: 'X', 'Y' or 'Z'
surf = False  # Keep only surfaces?

dx = (xmax - xmin)
dy = (ymax - ymin)
dz = (zmax - zmin)
L = dz if (dir == 'X') else dx
H = dz if (dir == 'Y') else dy

# Create the first cutting plane:
s = []
s.append((2, gmsh.model.occ.addRectangle(xmin, ymin, zmin, L, H)))
if dir == 'X':
    gmsh.model.occ.rotate([s[0]], xmin, ymin, zmin, 0, 1, 0, -math.pi/2)
elif dir == 'Y':
    gmsh.model.occ.rotate([s[0]], xmin, ymin, zmin, 1, 0, 0, math.pi/2)
tx = dx / N if (dir == 'X') else 0
ty = dy / N if (dir == 'Y') else 0
tz = dz / N if (dir == 'Z') else 0
gmsh.model.occ.translate([s[0]], tx, ty, tz)

# Create the other cutting planes:
for i in range(1, N-1):
    s.extend(gmsh.model.occ.copy([s[0]]))
    gmsh.model.occ.translate([s[-1]], i * tx, i * ty, i * tz)

# Fragment (i.e. intersect) the volume with all the cutting planes:
gmsh.model.occ.fragment(v, s)

# Now remove all the surfaces (and their bounding entities) that are not on the
# boundary of a volume, i.e. the parts of the cutting planes that "stick out" of
# the volume:
gmsh.model.occ.remove(gmsh.model.occ.getEntities(2), True)

gmsh.model.occ.synchronize()

if surf:
    # If we want to only keep the surfaces, retrieve the surfaces in bounding
    # boxes around the cutting planes...
    eps = 1e-4
    s = []
    for i in range(1, N):
        xx = xmin if (dir == 'X') else xmax
        yy = ymin if (dir == 'Y') else ymax
        zz = zmin if (dir == 'Z') else zmax
        s.extend(gmsh.model.getEntitiesInBoundingBox(
            xmin - eps + i * tx, ymin - eps + i * ty, zmin - eps + i * tz,
            xx + eps + i * tx, yy + eps + i * ty, zz + eps + i * tz, 2))
    # ...and remove all the other entities (here directly in the model, as we
    # won't modify any OpenCASCADE entities later on):
    dels = gmsh.model.getEntities(2)
    for e in s:
        dels.remove(e)
    gmsh.model.removeEntities(gmsh.model.getEntities(3))
    gmsh.model.removeEntities(dels)
    gmsh.model.removeEntities(gmsh.model.getEntities(1))
    gmsh.model.removeEntities(gmsh.model.getEntities(0))

# Finally, let's specify a global mesh size and mesh the partitioned model:
gmsh.option.setNumber("Mesh.MeshSizeMin", 3)
gmsh.option.setNumber("Mesh.MeshSizeMax", 3)
gmsh.model.mesh.generate(3)
gmsh.write("t20.msh")

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
