import gmsh
import sys

gmsh.initialize(sys.argv)

# create a simple cartesian grid (you can make it finer e.g. by passing
# "-clscale 0.01" on the command line)
gmsh.model.add("square")
gmsh.model.occ.addRectangle(0, 0, 0, 1, 1, 100)
gmsh.model.occ.synchronize()
gmsh.model.mesh.setTransfiniteSurface(100)
gmsh.model.mesh.generate(2)

# create a post-processing dataset
gmsh.plugin.setNumber("NewView", "Value", 1.234)
t = gmsh.plugin.run("NewView")

# retrieve the dataset as a vector of vectors (one for each tag)
print("before get")
type, tags, data, time, numComp = gmsh.view.getModelData(t, 0)
print("after get")

# retrieve the dataset as a single vector (muuuuch faster for Python)
print("before getHomogeneous")
type2, tags2, data2, time2, numComp2 = gmsh.view.getHomogeneousModelData(t, 0)
print("after getHomogeneous")

gmsh.finalize()
