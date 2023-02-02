import gmsh
import sys

gmsh.initialize(sys.argv)

gmsh.model.occ.addBox(0,0,0, 1,1,1)
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(3)

# get element qualities:
_, eleTags , _ = gmsh.model.mesh.getElements(dim=3)
q = gmsh.model.mesh.getElementQualities(eleTags[0], "minSICN")
print(zip(eleTags[0], q))

# alternative using plugin:
gmsh.plugin.setNumber("AnalyseMeshQuality", "ICNMeasure", 1.)
gmsh.plugin.setNumber("AnalyseMeshQuality", "CreateView", 1.)
t = gmsh.plugin.run("AnalyseMeshQuality")
dataType, tags, data, time, numComp = gmsh.view.getModelData(t, 0)
print('ICN for element {0} = {1}'.format(tags[0], data[0]))

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
