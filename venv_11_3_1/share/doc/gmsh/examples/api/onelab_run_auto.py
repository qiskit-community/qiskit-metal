import gmsh
import sys

# This shows how ONELAB clients that communicate with the ONELAB server through
# sockets can be executed using the Gmsh API, using client information stored in
# the "Solver.Name?", "Solver.Extension?" and ""Solver.Executable?" Gmsh options

# By default Gmsh defines Solver.Name0 = "GetDP" and Solver.Extension0 = ".pro".
# Provided that Solver.Executable0 points to the GetDP executable, if you open a
# file with the ".pro" extension with gmsh.open(), then call gmsh.onelab.run(),
# the getdp solver will be run.

# If Solver.Executable0 is not set, you can set it using
#
# gmsh.option.setString('Solver.Executable0', '/path/to/getdp')

if len(sys.argv) < 2:
    print("Usage: " + sys.argv[0] + " file [options]")
    exit(0)

gmsh.initialize()

gmsh.open(sys.argv[1])

# attempts to run a client selected when opening the file (e.g. a .pro file)
gmsh.onelab.run()

json = gmsh.onelab.get()
print(json)

gmsh.finalize()
