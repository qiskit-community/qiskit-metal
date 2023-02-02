# ------------------------------------------------------------------------------
#
#  Gmsh Python tutorial 8
#
#  Post-processing and animations
#
# ------------------------------------------------------------------------------

import gmsh
import os
import sys

# In addition to creating geometries and meshes, the Python API can also be used
# to manipulate post-processing datasets (called "views" in Gmsh).

gmsh.initialize()

# We first create a simple geometry
lc = 1e-2
gmsh.model.geo.addPoint(0, 0, 0, lc, 1)
gmsh.model.geo.addPoint(.1, 0, 0, lc, 2)
gmsh.model.geo.addPoint(.1, .3, 0, lc, 3)
gmsh.model.geo.addPoint(0, .3, 0, lc, 4)
gmsh.model.geo.addLine(1, 2, 1)
gmsh.model.geo.addLine(3, 2, 2)
gmsh.model.geo.addLine(3, 4, 3)
gmsh.model.geo.addLine(4, 1, 4)
gmsh.model.geo.addCurveLoop([4, 1, -2, 3], 1)
gmsh.model.geo.addPlaneSurface([1], 1)

gmsh.model.geo.synchronize()

# We merge some post-processing views to work on
path = os.path.dirname(os.path.abspath(__file__))
gmsh.merge(os.path.join(path, os.pardir, 'view1.pos'))
gmsh.merge(os.path.join(path, os.pardir, 'view1.pos'))
gmsh.merge(os.path.join(path, os.pardir, 'view4.pos'))  # contains 2 views inside

# Gmsh can read post-processing views in various formats. Here the `view1.pos'
# and `view4.pos' files are in the Gmsh "parsed" format, which is interpreted by
# the GEO script parser. The parsed format should only be used for relatively
# small datasets of course: for larger datasets using e.g. MSH files is much
# more efficient. Post-processing views can also be created directly from the
# Python API.

# We then set some general options:
gmsh.option.setNumber("General.Trackball", 0)
gmsh.option.setNumber("General.RotationX", 0)
gmsh.option.setNumber("General.RotationY", 0)
gmsh.option.setNumber("General.RotationZ", 0)

white = (255, 255, 255)
black = (0, 0, 0)

# Color options are special
# Setting a color option of "X.Y" actually sets the option "X.Color.Y"
# Sets "General.Color.Background", etc.
gmsh.option.setColor("General.Background", white[0], white[1], white[2])
gmsh.option.setColor("General.Foreground", black[0], black[1], black[2])
gmsh.option.setColor("General.Text", black[0], black[1], black[2])

gmsh.option.setNumber("General.Orthographic", 0)
gmsh.option.setNumber("General.Axes", 0)
gmsh.option.setNumber("General.SmallAxes", 0)

# Show the GUI:
if '-nopopup' not in sys.argv:
    gmsh.fltk.initialize()

# We also set some options for each post-processing view:

# If we were to follow the geo example blindly, we would read the number of
# views from the relevant option value, and use the gmsh.option.setNumber() and
# gmsh.option.setString() functions. A nicer way is to use gmsh.view.getTags()
# and to use the gmsh.view.option.setNumber() and gmsh.view.option.setString()
# functions.
v = gmsh.view.getTags()
if len(v) != 4:
    gmsh.logger.write("Wrong number of views!", "error")
    gmsh.finalize()
    exit()

# We set some options for each post-processing view:
gmsh.view.option.setNumber(v[0], "IntervalsType", 2)
gmsh.view.option.setNumber(v[0], "OffsetZ", 0.05)
gmsh.view.option.setNumber(v[0], "RaiseZ", 0)
gmsh.view.option.setNumber(v[0], "Light", 1)
gmsh.view.option.setNumber(v[0], "ShowScale", 0)
gmsh.view.option.setNumber(v[0], "SmoothNormals", 1)

gmsh.view.option.setNumber(v[1], "IntervalsType", 1)
# Note that we can't yet set the ColorTable in API
gmsh.view.option.setNumber(v[1], "NbIso", 10)
gmsh.view.option.setNumber(v[1], "ShowScale", 0)

gmsh.view.option.setString(v[2], "Name", "Test...")
gmsh.view.option.setNumber(v[2], "Axes", 1)
gmsh.view.option.setNumber(v[2], "IntervalsType", 2)
gmsh.view.option.setNumber(v[2], "Type", 2)
gmsh.view.option.setNumber(v[2], "IntervalsType", 2)
gmsh.view.option.setNumber(v[2], "AutoPosition", 0)
gmsh.view.option.setNumber(v[2], "PositionX", 85)
gmsh.view.option.setNumber(v[2], "PositionY", 50)
gmsh.view.option.setNumber(v[2], "Width", 200)
gmsh.view.option.setNumber(v[2], "Height", 130)

gmsh.view.option.setNumber(v[3], "Visible", 0)

# You can save an MPEG movie directly by selecting `File->Export' in the
# GUI. Several predefined animations are setup, for looping on all the time
# steps in views, or for looping between views.

# But the API can be used to build much more complex animations, by changing
# options at run-time and re-rendering the graphics. Each frame can then be
# saved to disk as an image, and multiple frames can be encoded to form a
# movie. Below is an example of such a custom animation.

t = 0  # Initial step

for num in range(1, 4):

    # Set time step
    for vv in v:
        gmsh.view.option.setNumber(vv, "TimeStep", t)

    current_step = gmsh.view.option.getNumber(v[0], "TimeStep")
    max_step = gmsh.view.option.getNumber(v[0], "NbTimeStep") - 1
    if current_step < max_step:
        t = t + 1
    else:
        t = 0

    gmsh.view.option.setNumber(v[0], "RaiseZ",
                               gmsh.view.option.getNumber(v[0], "RaiseZ") +
                               0.01 / gmsh.view.option.getNumber(v[0], "Max") * t)

    if num == 3:
        # Resize the graphics when num == 3, to create 640x480 frames
        gmsh.option.setNumber("General.GraphicsWidth",
                              gmsh.option.getNumber("General.MenuWidth") + 640)
        gmsh.option.setNumber("General.GraphicsHeight", 480)

    frames = 50
    for num2 in range(frames):
        # Incrementally rotate the scene
        gmsh.option.setNumber("General.RotationX",
                              gmsh.option.getNumber("General.RotationX") + 10)
        gmsh.option.setNumber("General.RotationY",
                              gmsh.option.getNumber("General.RotationX") / 3)
        gmsh.option.setNumber("General.RotationZ",
                              gmsh.option.getNumber("General.RotationZ") + 0.1)

        # Draw the scene
        gmsh.graphics.draw()

        if num == 3:
            # Uncomment the following lines to save each frame to an image file

            # gmsh.write("t8-{}.gif".format(num2))
            # gmsh.write("t8-{}.ppm".format(num2))
            # gmsh.write("t8-{}.jpg".format(num2))
            pass

    if num == 3:
        # Here we could make a system call to generate a movie. For example,
        # with ffmeg:

        # import subprocess
        # subprocess.call("ffmpeg -i t8-%d.jpg t8.mpg".split(' '))
        pass

if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
