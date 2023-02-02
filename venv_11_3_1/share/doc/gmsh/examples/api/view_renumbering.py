import gmsh
import sys

# test that mesh renumbering also correctly renumbers all dependent model-based
# views

gmsh.initialize(sys.argv)

gmsh.model.add("simple model")
surf = gmsh.model.addDiscreteEntity(2)

gmsh.model.mesh.addNodes(2, surf, [11, 12, 13, 14],
                         [0., 0., 0., 1., 0., 0., 1., 1., 0., 0., 1., 0.])
gmsh.model.mesh.addElementsByType(surf, 2, [100, 102], [11, 12, 13, 11, 13, 14])

t1 = gmsh.view.add("A nodal view")
for step in range(0, 10):
    gmsh.view.addHomogeneousModelData(
        t1, step, "simple model", "NodeData",
        [11, 12, 13, 14],  # tags of nodes
        [10., 10., 12. + step, 13. + step])  # data, per node

t2 = gmsh.view.add("An element view")
gmsh.view.addHomogeneousModelData(
    t2, 0, "simple model", "ElementData",
    [100, 102],  # tags of elements
    [3.14, 6.28])  # data, per element

# renumber nodes and elements - the views should be automatically renumbered as
# well
gmsh.model.mesh.renumberNodes()
gmsh.model.mesh.renumberElements()

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
