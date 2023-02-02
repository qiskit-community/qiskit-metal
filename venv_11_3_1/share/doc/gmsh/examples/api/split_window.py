import gmsh
import sys

if '-nopopup' in sys.argv:
    exit(0)

gmsh.initialize(sys.argv)

# create simple geometry
gmsh.model.occ.addBox(-3, -2, -1, 6, 4, 2)
gmsh.model.occ.synchronize()

gmsh.option.setNumber("Mesh.SurfaceFaces", 1)

# launch GUI
gmsh.fltk.initialize()

# split window 50%-50% horizontally and change the rotation;
# rotation/translation/scale options are applied to the current subwindow (the
# last one created)
gmsh.fltk.splitCurrentWindow('h', 0.5)
gmsh.option.setNumber("General.Trackball", 0)
gmsh.option.setNumber("General.RotationX", -90)
gmsh.option.setNumber("General.RotationY", 0)
gmsh.option.setNumber("General.RotationZ", -90)

# split the current subwindow into two parts, vertically and change the rotation
gmsh.fltk.splitCurrentWindow('v', 0.5)
gmsh.option.setNumber("General.RotationX", -90)
gmsh.option.setNumber("General.RotationY", 0)
gmsh.option.setNumber("General.RotationZ", 180)

# change the current window to the original one (subwindows are indexed starting
# from 0; new subwindows created by splitCurrentWindow() are appended at the
# end), and adjust rotation
gmsh.fltk.setCurrentWindow(0)
gmsh.option.setNumber("General.RotationX", -75)
gmsh.option.setNumber("General.RotationY", -25)

# mesh the model
gmsh.model.mesh.generate(2)

# redraw
gmsh.graphics.draw()

# save all subwindows into a composite PNG
gmsh.option.setNumber("Print.CompositeWindows", 1)
gmsh.write("img_composite.png")

# restore single window
gmsh.fltk.splitCurrentWindow('u')
gmsh.write("img_single.png")

gmsh.finalize()
