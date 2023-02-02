import gmsh
import os
import sys

gmsh.initialize()

# load step file
path = os.path.dirname(os.path.abspath(__file__))
gmsh.open(os.path.join(path, 'as1-tu-203.stp'))

gmsh.model.occ.removeAllDuplicates()
gmsh.model.occ.synchronize()

# set STL generation options
gmsh.option.setNumber('Mesh.StlLinearDeflection', 1)
gmsh.option.setNumber('Mesh.StlLinearDeflectionRelative', 0)
gmsh.option.setNumber('Mesh.StlAngularDeflection', 0.5)

# import the model STL as a mesh
gmsh.model.mesh.importStl()
gmsh.model.mesh.removeDuplicateNodes()
#gmsh.model.mesh.reclassifyNodes()

# create quads
gmsh.option.setNumber('Mesh.RecombinationAlgorithm', 0)
gmsh.option.setNumber('Mesh.RecombineOptimizeTopology', 0)
gmsh.option.setNumber('Mesh.RecombineNodeRepositioning', 0)
gmsh.option.setNumber('Mesh.RecombineMinimumQuality', 1e-3)
gmsh.model.mesh.recombine()

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
