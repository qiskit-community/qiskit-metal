import gmsh
import sys

gmsh.initialize()

# create a model with OCC and mesh it
gmsh.model.add('model1')
gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(3)

# the goal is to create a second discrete model that contains a copy of the mesh
# (e.g. to deform it, or to use it a background mesh on which optimal mesh sizes
# are computed)

# 1) store the mesh
m = {}
for e in gmsh.model.getEntities():
    m[e] = (gmsh.model.getBoundary([e]),
            gmsh.model.mesh.getNodes(e[0], e[1]),
            gmsh.model.mesh.getElements(e[0], e[1]))

# 2) create a new model
gmsh.model.add('model2')

# 3) create discrete entities in the new model and copy the mesh
for e in sorted(m):
    gmsh.model.addDiscreteEntity(e[0], e[1], [b[1] for b in m[e][0]])
    gmsh.model.mesh.addNodes(e[0], e[1], m[e][1][0], m[e][1][1])
    gmsh.model.mesh.addElements(e[0], e[1], m[e][2][0], m[e][2][1], m[e][2][2])


# application example: say we want to mesh model1 with a mesh size inferred by
# some error estimation computed on its mesh, stored as a post-processing view
# based on this mesh. We need a copy of the mesh: otherwise the support of the
# post-processing view will be destroyed when we remesh.

# 4) so we create a post-processing view based on the mesh copy (i.e. on model2)
view = gmsh.view.add('bgView')
nodes = gmsh.model.mesh.getNodes()
gmsh.view.addHomogeneousModelData(view, 0, 'model2', 'NodeData',
                                  nodes[0], nodes[1][::3]/10.+0.01)

# 5) we create the mesh size field for model1, based on the view based on model2
gmsh.model.setCurrent('model1')
field = gmsh.model.mesh.field.add("PostView")
gmsh.model.mesh.field.setNumber(field, "ViewTag", view)
gmsh.model.mesh.field.setAsBackgroundMesh(field)

# 6) and we mesh model1 a second time, using the mesh size field
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.Algorithm3D", 10)
gmsh.model.mesh.clear()
gmsh.model.mesh.generate(3)

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
