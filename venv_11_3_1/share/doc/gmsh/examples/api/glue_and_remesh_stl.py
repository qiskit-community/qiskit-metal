import gmsh
import math
import os
import sys

gmsh.initialize()

# load two STL surfaces
path = os.path.dirname(os.path.abspath(__file__))
gmsh.merge(os.path.join(path, 'surface1.stl'))
gmsh.merge(os.path.join(path, 'surface2.stl'))

# merge nodes that are at the same position up to some tol
gmsh.option.setNumber('Geometry.Tolerance', 1e-4)
gmsh.model.mesh.removeDuplicateNodes()

# classify surface mesh according to given angle, and create discrete model
# entities (surfaces, curves and points) accordingly
gmsh.model.mesh.classifySurfaces(math.pi / 2)

# Notes:
#
# - for more complicated surfaces `forReparametrization=True` could be specified
# to force the creation of reparametrizable patches
#
# - in this simple case, since the two surfaces were simple and already colored,
# one could have also simply used `gmsh.model.mesh.createTopology()` instead of
# `gmsh.model.mesh.classifySurfaces()`

# create a geometry for the discrete curves and surfaces (comment this if you
# don't want to remesh the surfaces and simply use the original mesh)
gmsh.model.mesh.createGeometry()

# get all the surfaces in the model
s = gmsh.model.getEntities(2)

# create a surface loop and a volume from these surfaces
l = gmsh.model.geo.addSurfaceLoop([e[1] for e in s])
gmsh.model.geo.addVolume([l])

# synchronize the new volume with the model
gmsh.model.geo.synchronize()

# mesh
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.option.setNumber("Mesh.MeshSizeMin", 0.4)
gmsh.option.setNumber("Mesh.MeshSizeMax", 0.4)
gmsh.model.mesh.generate(3)

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()
gmsh.finalize()
