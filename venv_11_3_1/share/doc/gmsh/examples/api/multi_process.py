from multiprocessing import Process
import gmsh

# to mesh independent entities you can of course run multiple independent Gmsh
# processes as well (cf. multi_thread.py for actual parallel mesh generation)

def f(i):
    gmsh.initialize()
    s = gmsh.model.occ.addRectangle(i,0,0, 1,1)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMax', 0.005)
    gmsh.model.mesh.generate(2)
    gmsh.finalize()

if __name__ == '__main__':
    procs = []
    for i in range(5):
        p = Process(target=f, args=(i,))
        p.start()
        procs.append(p)
    for p in procs: p.join()
    print("All done")
