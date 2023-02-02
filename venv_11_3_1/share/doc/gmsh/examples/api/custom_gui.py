import gmsh
import math
import time
import threading
import sys

# This example shows how to implement a custom user interface running
# computationally expensive calculations in separate threads. The threads can
# update the user interface in real-time.

gmsh.initialize()

# hide the standard Gmsh modules
gmsh.option.setNumber("General.ShowModuleMenu", 0)

# don't print messages on the terminal
gmsh.option.setNumber("General.Terminal", 0)

# create some ONELAB parameters to control the number of iterations and
# threads, the progress display and the custom ONELAB button (when pressed,
# it will set the "ONELAB/Action" parameter to "should compute")
parameters = """
[
  { "type":"number", "name":"My App/Iterations", "values":[1e6], "min":1e4,
    "max":1e9, "step":1e5, "attributes":{"Highlight":"AliceBlue"} },
  { "type":"number", "name":"My App/Number of threads", "values":[2],
    "min":1, "max":16, "step":1, "attributes":{"Highlight":"AliceBlue"} },
  { "type":"number", "name":"My App/Show progress?", "values":[1],
    "choices":[0, 1] },
  { "type":"string", "name":"ONELAB/Button", "values":["Do it!", "should compute"],
    "visible":false }
]"""
gmsh.onelab.set(parameters)

# flag that will be set to interrupt a calculation
stop_computation = False


# a computationally expensive routine, that will be run in its own thread
def compute(arg):
    iterations = gmsh.onelab.getNumber("My App/Iterations")
    progress = gmsh.onelab.getNumber("My App/Show progress?")
    n = int(iterations[0]) if len(iterations) > 0 else 1
    show = True if (len(progress) > 0 and progress[0] == 1) else False
    p = 0
    k = 0
    last_refresh = -1
    for j in range(n):
        # stop computation if requested by clicking on "Stop it!"
        if stop_computation:
            break
        k = math.sin(k) + math.cos(j / 45.)
        # show progress in real time?
        if (show == 1) and (n > 1) and (not j % (n / 100)):
            p = p + 1
            gmsh.onelab.setString(arg, ["{0}%".format(p)])
            # any code in a thread other than the main thread that modifies the
            # user interface should be locked
            gmsh.fltk.lock()
            gmsh.logger.write("{0} progress {1}%".format(arg, p))
            gmsh.fltk.unlock()
            # ask the main thread to process pending events and to update
            # the user interface
            if time.time() - last_refresh > 0.1:
                last_refresh = time.time()
                gmsh.fltk.awake("update")
    gmsh.onelab.setNumber(arg + " result", [k])
    gmsh.onelab.setString("ONELAB/Action", ["done computing"])
    gmsh.fltk.awake("update")
    return


def checkForEvent():
    # check if an action is requested
    action = gmsh.onelab.getString("ONELAB/Action")
    global stop_computation
    if len(action) < 1:
        # no action requested
        pass
    elif action[0] == "should compute":
        gmsh.onelab.setString("ONELAB/Action", [""])
        gmsh.onelab.setString("ONELAB/Button", ["Stop!", "should stop"])
        # force interface update (to show the new button label)
        gmsh.fltk.update()
        # start computationally intensive calculations in their own threads
        n = int(gmsh.onelab.getNumber("My App/Number of threads")[0])
        for i in range(n):
            t = threading.Thread(target=compute,
                                 args=("My App/Thread {0}".format(i + 1), ))
            t.start()
    elif action[0] == "should stop":
        stop_computation = True
    elif action[0] == "done computing":
        gmsh.onelab.setString("ONELAB/Action", [""])
        gmsh.onelab.setString("ONELAB/Button", ["Do it!", "should compute"])
        gmsh.fltk.update()
        stop_computation = False
    elif action[0] == "reset":
        # user clicked on "Reset database"
        gmsh.onelab.setString("ONELAB/Action", [""])
        gmsh.onelab.set(parameters)
        gmsh.fltk.update()
    elif action[0] == "check":
        # could perform action here after each change in ONELAB parameters,
        # e.g. rebuild a CAD model, update other parameters, ...
        pass
    return 1


# create the graphical user interface
if "-nopopup" not in sys.argv:
    gmsh.fltk.initialize()
    # wait for events until the GUI is closed
    while gmsh.fltk.isAvailable() and checkForEvent():
        gmsh.fltk.wait()

gmsh.finalize()
