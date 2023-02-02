import gmsh

# when Gmsh is compiled with OpenMP support the meshing pipeline is
# multi-threaded; the number of threads is governed by the "General.NumThreads"
# option (cf. multi_process.py for parallel meshing of independent models)

gmsh.initialize()

for i in range(5):
    s = gmsh.model.occ.addRectangle(i,0,0, 1,1)

gmsh.model.occ.synchronize()
gmsh.option.setNumber('Mesh.MeshSizeMax', 0.005)
gmsh.option.setNumber('General.NumThreads', 5)
gmsh.model.mesh.generate(2)
gmsh.finalize()
print("All done")
