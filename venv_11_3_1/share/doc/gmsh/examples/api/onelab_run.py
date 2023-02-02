import gmsh
import threading
import sys

# This shows how ONELAB clients that communicate with the ONELAB server through
# sockets can be executed using the Gmsh API, by explicitly specying the
# command to run the client

# One such example is the GetDP finite element solver (https://getdp.info).

# Provided that the getdp executable is in your path, running this example in
# the getdp/demos directory will launch two getdp clients concurrently, that
# will both exchange data with the ONELAB server

gmsh.initialize()

# set a parameter in the onelab database
gmsh.onelab.setNumber('Parameters/Materials/hc', [920000. / 2.])

# run the getdp client (which will connect through a socket), by forcing the
# value of murCore
def compute(name, value):
    cmd = 'getdp magnet.pro -solve Magnetostatics_phi -setnumber murCore {}'
    gmsh.onelab.run(name, cmd.format(value))
    return

# run the two calculations in parallel
t1 = threading.Thread(target=compute, args=('my first getdp', 20))
t1.start()
t2 = threading.Thread(target=compute, args=('my second getdp', 1000))
t2.start()

# wait for the 2 calculations to stop
t1.join()
t2.join()

gmsh.finalize()
