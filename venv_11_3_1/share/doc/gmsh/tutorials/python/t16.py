# ------------------------------------------------------------------------------
#
#  Gmsh Python tutorial 16
#
#  Constructive Solid Geometry, OpenCASCADE geometry kernel
#
# ------------------------------------------------------------------------------

# Instead of constructing a model in a bottom-up fashion with Gmsh's built-in
# geometry kernel, starting with version 3 Gmsh allows you to directly use
# alternative geometry kernels. Here we will use the OpenCASCADE kernel.

import gmsh
import math
import sys

gmsh.initialize()

gmsh.model.add("t16")

# Let's build the same model as in `t5.py', but using constructive solid
# geometry.

# We can log all messages for further processing with:
gmsh.logger.start()

# We first create two cubes:
gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1, 1)
gmsh.model.occ.addBox(0, 0, 0, 0.5, 0.5, 0.5, 2)

# We apply a boolean difference to create the "cube minus one eigth" shape:
gmsh.model.occ.cut([(3, 1)], [(3, 2)], 3)

# Boolean operations with OpenCASCADE always create new entities. By default the
# extra arguments `removeObject' and `removeTool' in `cut()' are set to `True',
# which will delete the original entities.

# We then create the five spheres:
x = 0
y = 0.75
z = 0
r = 0.09
holes = []
for t in range(1, 6):
    x += 0.166
    z += 0.166
    gmsh.model.occ.addSphere(x, y, z, r, 3 + t)
    holes.append((3, 3 + t))

# If we had wanted five empty holes we would have used `cut()' again. Here we
# want five spherical inclusions, whose mesh should be conformal with the mesh
# of the cube: we thus use `fragment()', which intersects all volumes in a
# conformal manner (without creating duplicate interfaces):
ov, ovv = gmsh.model.occ.fragment([(3, 3)], holes)

# ov contains all the generated entities of the same dimension as the input
# entities:
print("fragment produced volumes:")
for e in ov:
    print(e)

# ovv contains the parent-child relationships for all the input entities:
print("before/after fragment relations:")
for e in zip([(3, 3)] + holes, ovv):
    print("parent " + str(e[0]) + " -> child " + str(e[1]))

gmsh.model.occ.synchronize()

# When the boolean operation leads to simple modifications of entities, and if
# one deletes the original entities, Gmsh tries to assign the same tag to the
# new entities. (This behavior is governed by the
# `Geometry.OCCBooleanPreserveNumbering' option.)

# Here the `Physical Volume' definitions can thus be made for the 5 spheres
# directly, as the five spheres (volumes 4, 5, 6, 7 and 8), which will be
# deleted by the fragment operations, will be recreated identically (albeit with
# new surfaces) with the same tags:
for i in range(1, 6):
    gmsh.model.addPhysicalGroup(3, [3 + i], i)

# The tag of the cube will change though, so we need to access it
# programmatically:
gmsh.model.addPhysicalGroup(3, [ov[-1][1]], 10)

# Creating entities using constructive solid geometry is very powerful, but can
# lead to practical issues for e.g. setting mesh sizes at points, or identifying
# boundaries.

# To identify points or other bounding entities you can take advantage of the
# `getEntities()', `getBoundary()' and `getEntitiesInBoundingBox()' functions:

lcar1 = .1
lcar2 = .0005
lcar3 = .055

# Assign a mesh size to all the points:
gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lcar1)

# Override this constraint on the points of the five spheres:
gmsh.model.mesh.setSize(gmsh.model.getBoundary(holes, False, False, True),
                        lcar3)

# Select the corner point by searching for it geometrically:
eps = 1e-3
ov = gmsh.model.getEntitiesInBoundingBox(0.5 - eps, 0.5 - eps, 0.5 - eps,
                                         0.5 + eps, 0.5 + eps, 0.5 + eps, 0)
gmsh.model.mesh.setSize(ov, lcar2)

gmsh.model.mesh.generate(3)

gmsh.write("t16.msh")

# Additional examples created with the OpenCASCADE geometry kernel are available
# in `t18.py', `t19.py' and `t20.py', as well as in the `examples/api'
# directory.

# Inspect the log:
log = gmsh.logger.get()
print("Logger has recorded " + str(len(log)) + " lines")
gmsh.logger.stop()

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
