import gmsh

if length(ARGS) < 1
    println("Usage: julia explore.jl file.msh")
    exit(0)
end

gmsh.initialize()
gmsh.open(ARGS[1])

# get all elementary entities in the model
entities = gmsh.model.getEntities()

for e in entities
    # get the mesh nodes for each elementary entity
    nodeTags, nodeCoords, nodeParams = gmsh.model.mesh.getNodes(e[1], e[2])
    # get the mesh elements for each elementary entity
    elemTypes, elemTags, elemNodeTags = gmsh.model.mesh.getElements(e[1], e[2])
    # report some statistics
    numElem = sum([length(t) for t in elemTags])
    println(length(nodeTags), " mesh nodes and ", numElem, " mesh elements ",
            "on entity ", e, " of type ", gmsh.model.getType(e[1], e[2]))
    partitions = gmsh.model.getPartitions(e[1], e[2])
    if length(partitions) > 0
        println(" - Partition tag(s): ", partitions, " - parent entity",
                gmsh.model.getParent(e[1], e[2]))
    end
    for t in elemTypes
        name, dim, order, numv, parv = gmsh.model.mesh.getElementProperties(t)
        println(" - Element type: ", name, ", order ", order)
        println("   with ", numv, " nodes in param coord: ", parv)
    end
end

gmsh.finalize()
