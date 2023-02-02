# ------------------------------------------------------------------------------
#
#  Gmsh Python tutorial 10
#
#  Mesh size fields
#
# ------------------------------------------------------------------------------

# In addition to specifying target mesh sizes at the points of the geometry (see
# `t1.py') or using a background mesh (see `t7.py'), you can use general mesh
# size "Fields".

import gmsh
import sys

gmsh.initialize(sys.argv)

gmsh.model.add("t10")

# Let's create a simple rectangular geometry:
lc = .15
gmsh.model.geo.addPoint(0.0, 0.0, 0, lc, 1)
gmsh.model.geo.addPoint(1, 0.0, 0, lc, 2)
gmsh.model.geo.addPoint(1, 1, 0, lc, 3)
gmsh.model.geo.addPoint(0, 1, 0, lc, 4)
gmsh.model.geo.addPoint(0.2, .5, 0, lc, 5)

gmsh.model.geo.addLine(1, 2, 1)
gmsh.model.geo.addLine(2, 3, 2)
gmsh.model.geo.addLine(3, 4, 3)
gmsh.model.geo.addLine(4, 1, 4)

gmsh.model.geo.addCurveLoop([1, 2, 3, 4], 5)
gmsh.model.geo.addPlaneSurface([5], 6)

gmsh.model.geo.synchronize()

# Say we would like to obtain mesh elements with size lc/30 near curve 2 and
# point 5, and size lc elsewhere. To achieve this, we can use two fields:
# "Distance", and "Threshold". We first define a Distance field (`Field[1]') on
# points 5 and on curve 2. This field returns the distance to point 5 and to
# (100 equidistant points on) curve 2.
gmsh.model.mesh.field.add("Distance", 1)
gmsh.model.mesh.field.setNumbers(1, "PointsList", [5])
gmsh.model.mesh.field.setNumbers(1, "CurvesList", [2])
gmsh.model.mesh.field.setNumber(1, "Sampling", 100)

# We then define a `Threshold' field, which uses the return value of the
# `Distance' field 1 in order to define a simple change in element size
# depending on the computed distances
#
# SizeMax -                     /------------------
#                              /
#                             /
#                            /
# SizeMin -o----------------/
#          |                |    |
#        Point         DistMin  DistMax
gmsh.model.mesh.field.add("Threshold", 2)
gmsh.model.mesh.field.setNumber(2, "InField", 1)
gmsh.model.mesh.field.setNumber(2, "SizeMin", lc / 30)
gmsh.model.mesh.field.setNumber(2, "SizeMax", lc)
gmsh.model.mesh.field.setNumber(2, "DistMin", 0.15)
gmsh.model.mesh.field.setNumber(2, "DistMax", 0.5)

# Say we want to modulate the mesh element sizes using a mathematical function
# of the spatial coordinates. We can do this with the MathEval field:
gmsh.model.mesh.field.add("MathEval", 3)
gmsh.model.mesh.field.setString(3, "F",
                                "Cos(4*3.14*x) * Sin(4*3.14*y) / 10 + 0.101")

# We could also combine MathEval with values coming from other fields. For
# example, let's define a `Distance' field around point 1
gmsh.model.mesh.field.add("Distance", 4)
gmsh.model.mesh.field.setNumbers(4, "PointsList", [1])

# We can then create a `MathEval' field with a function that depends on the
# return value of the `Distance' field 4, i.e., depending on the distance to
# point 1 (here using a cubic law, with minimum element size = lc / 100)
gmsh.model.mesh.field.add("MathEval", 5)
gmsh.model.mesh.field.setString(5, "F", "F4^3 + " + str(lc / 100))

# We could also use a `Box' field to impose a step change in element sizes
# inside a box
gmsh.model.mesh.field.add("Box", 6)
gmsh.model.mesh.field.setNumber(6, "VIn", lc / 15)
gmsh.model.mesh.field.setNumber(6, "VOut", lc)
gmsh.model.mesh.field.setNumber(6, "XMin", 0.3)
gmsh.model.mesh.field.setNumber(6, "XMax", 0.6)
gmsh.model.mesh.field.setNumber(6, "YMin", 0.3)
gmsh.model.mesh.field.setNumber(6, "YMax", 0.6)
gmsh.model.mesh.field.setNumber(6, "Thickness", 0.3)

# Many other types of fields are available: see the reference manual for a
# complete list. You can also create fields directly in the graphical user
# interface by selecting `Define->Size fields' in the `Mesh' module.

# Let's use the minimum of all the fields as the background mesh field:
gmsh.model.mesh.field.add("Min", 7)
gmsh.model.mesh.field.setNumbers(7, "FieldsList", [2, 3, 5, 6])

gmsh.model.mesh.field.setAsBackgroundMesh(7)

# The API also allows to set a global mesh size callback, which is called each
# time the mesh size is queried
def meshSizeCallback(dim, tag, x, y, z, lc):
    return min(lc, 0.02 * x + 0.01)

gmsh.model.mesh.setSizeCallback(meshSizeCallback)

# To determine the size of mesh elements, Gmsh locally computes the minimum of
#
# 1) the size of the model bounding box;
# 2) if `Mesh.MeshSizeFromPoints' is set, the mesh size specified at geometrical
#    points;
# 3) if `Mesh.MeshSizeFromCurvature' is positive, the mesh size based on
#    curvature (the value specifying the number of elements per 2 * pi rad);
# 4) the background mesh field;
# 5) any per-entity mesh size constraint;
#
# The value can then be further modified by the mesh size callback, if any,
# before being constrained in the interval [`Mesh.MeshSizeMin',
# `Mesh.MeshSizeMax'] and multiplied by `Mesh.MeshSizeFactor'.  In addition,
# boundary mesh sizes are interpolated inside surfaces and/or volumes depending
# on the value of `Mesh.MeshSizeExtendFromBoundary' (which is set by default).
#
# When the element size is fully specified by a background mesh (as it is in
# this example), it is thus often desirable to set

gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

# This will prevent over-refinement due to small mesh sizes on the boundary.

# Finally, while the default "Frontal-Delaunay" 2D meshing algorithm
# (Mesh.Algorithm = 6) usually leads to the highest quality meshes, the
# "Delaunay" algorithm (Mesh.Algorithm = 5) will handle complex mesh size fields
# better - in particular size fields with large element size gradients:

gmsh.option.setNumber("Mesh.Algorithm", 5)

gmsh.model.mesh.generate(2)
gmsh.write("t10.msh")

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
