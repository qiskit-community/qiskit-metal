import gmsh
import math

gmsh.initialize()

N = 2500

tic = gmsh.logger.getWallTime()

try:
    import numpy as np
    try:
        np.stack
    except:
        raise ImportError
    def create_mesh(N):
        l = np.linspace(0, 1, N + 1)
        x, y = np.meshgrid(l, l)
        z = 0.05 * np.sin(10 * (x + y))
        coords = np.stack([x, y, z], axis = 2)
        # tags of corresponding nodes
        nodes = np.arange(1, 1 + (N + 1)**2, 1, np.int32).reshape((N + 1, N + 1))
        # connectivities (node tags) of triangle elements
        tris = np.stack([nodes[:-1, :-1], nodes[1: , :-1], nodes[:-1, 1: ],
                         nodes[1: , :-1], nodes[1: , 1: ], nodes[:-1, 1: ]],
                        axis = 2)
        return coords.flat, nodes.flat, tris.flat

except ImportError:
    def create_mesh(N):
        coords = [0] * (N + 1) * (N + 1) * 3
        nodes = [0] * (N + 1) * (N + 1)
        tris = [0] * N * N * 2 * 3
        def get_node_tag(i, j):
            return (N + 1) * i + j + 1
        k = 0
        l = 0
        for i in range(N + 1):
            for j in range(N + 1):
                nodes[k] = get_node_tag(i, j)
                coords[3 * k] = float(i) / N
                coords[3 * k + 1] = float(j) / N
                coords[3 * k + 2] = 0.05 * math.sin(10 * float(i + j) / N)
                k = k + 1
                if i > 0 and j > 0:
                    tris[6 * l] = get_node_tag(i - 1, j - 1)
                    tris[6 * l + 1] = get_node_tag(i, j - 1)
                    tris[6 * l + 2] = get_node_tag(i - 1, j)
                    tris[6 * l + 3] = get_node_tag(i, j - 1)
                    tris[6 * l + 4] = get_node_tag(i, j)
                    tris[6 * l + 5] = get_node_tag(i - 1, j)
                    l = l + 1
        return coords, nodes, tris

coords, nodes, tris = create_mesh(N)
toc = gmsh.logger.getWallTime()
print("==> created nodes and connectivities in {} seconds".format(toc - tic))

tic = gmsh.logger.getWallTime()
surf = gmsh.model.addDiscreteEntity(2)
toc = gmsh.logger.getWallTime()
print("==> created surface in {} seconds".format(toc - tic))

tic = gmsh.logger.getWallTime()
gmsh.model.mesh.addNodes(2, 1, nodes, coords)
toc = gmsh.logger.getWallTime()
print("==> imported nodes in {} seconds".format(toc - tic))

tic = gmsh.logger.getWallTime()
gmsh.model.mesh.addElementsByType(1, 2, [], tris)
toc = gmsh.logger.getWallTime()
print("==> imported elements in {} seconds".format(toc - tic))

tic = gmsh.logger.getWallTime()
gmsh.option.setNumber("Mesh.Binary", 1)
gmsh.write("import_perf.msh")
toc = gmsh.logger.getWallTime()
print("==> wrote to disk in {} seconds".format(toc - tic))

tic = gmsh.logger.getWallTime()
gmsh.merge("import_perf.msh")
toc = gmsh.logger.getWallTime()
print("==> read from disk in {} seconds".format(toc - tic))

#gmsh.fltk.run()

gmsh.finalize()
