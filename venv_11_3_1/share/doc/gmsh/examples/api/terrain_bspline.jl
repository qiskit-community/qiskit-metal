import gmsh

gmsh.initialize()

gmsh.model.add("terrain")

# create the terrain surface from N x N input data points (here simulated using
# a simple function):
N = 100
ps = []

# create a bspline surface
for i in 0:N
    for j in 0:N
        push!(ps, gmsh.model.occ.addPoint(float(i) / N, float(j) / N,
                                          0.05 * sin(10 * float(i + j) / N)))
    end
end
s = gmsh.model.occ.addBSplineSurface(ps, N+1)

# create a box
v = gmsh.model.occ.addBox(0, 0, -0.5, 1, 1, 1)

# fragment the box with the bspline surface
gmsh.model.occ.fragment([(2, s)], [(3, v)])
gmsh.model.occ.synchronize()

# define a parameter to select the mesh type interactively
gmsh.onelab.set("""[
  {
    "type":"number",
    "name":"Parameters/Full-hex mesh?",
    "values":[0],
    "choices":[0, 1]
  }
]""")


function setMeshConstraint()
    if gmsh.onelab.getNumber("Parameters/Full-hex mesh?")[1] == 1
        NN = 30
        for c in gmsh.model.getEntities(1)
            gmsh.model.mesh.setTransfiniteCurve(c[2], NN)
            for s in gmsh.model.getEntities(2)
                gmsh.model.mesh.setTransfiniteSurface(s[2])
                gmsh.model.mesh.setRecombine(s[1], s[2])
                gmsh.model.mesh.setSmoothing(s[1], s[2], 100)
            end
        end
        gmsh.model.mesh.setTransfiniteVolume(1)
        gmsh.model.mesh.setTransfiniteVolume(2)
    else
        gmsh.model.mesh.removeConstraints()
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.05)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 0.05)
    end
end

setMeshConstraint()

function checkForEvent()
    action = gmsh.onelab.getString("ONELAB/Action")
    if length(action) > 0 && action[1] == "check"
        gmsh.onelab.setString("ONELAB/Action", [""])
        setMeshConstraint()
    end
    return true
end

if !("-nopopup" in ARGS)
    gmsh.fltk.initialize()
    while gmsh.fltk.isAvailable() == 1 && checkForEvent()
        gmsh.fltk.wait()
    end
end

gmsh.finalize()
