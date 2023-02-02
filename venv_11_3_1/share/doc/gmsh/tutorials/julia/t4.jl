# See the corresponding Python tutorial for detailed comments.

import gmsh

gmsh.initialize()

gmsh.model.add("t4")

cm = 1e-02
e1 = 4.5 * cm; e2 = 6 * cm / 2; e3 =  5 * cm / 2
h1 = 5 * cm; h2 = 10 * cm; h3 = 5 * cm; h4 = 2 * cm; h5 = 4.5 * cm
R1 = 1 * cm; R2 = 1.5 * cm; r = 1 * cm
Lc1 = 0.01
Lc2 = 0.003

function hypot(a, b)
    return sqrt(a * a + b * b)
end

ccos = (-h5*R1 + e2 * hypot(h5, hypot(e2, R1))) / (h5*h5 + e2*e2)
ssin = sqrt(1 - ccos*ccos)

factory = gmsh.model.geo
factory.addPoint(-e1-e2, 0    , 0, Lc1, 1)
factory.addPoint(-e1-e2, h1   , 0, Lc1, 2)
factory.addPoint(-e3-r , h1   , 0, Lc2, 3)
factory.addPoint(-e3-r , h1+r , 0, Lc2, 4)
factory.addPoint(-e3   , h1+r , 0, Lc2, 5)
factory.addPoint(-e3   , h1+h2, 0, Lc1, 6)
factory.addPoint( e3   , h1+h2, 0, Lc1, 7)
factory.addPoint( e3   , h1+r , 0, Lc2, 8)
factory.addPoint( e3+r , h1+r , 0, Lc2, 9)
factory.addPoint( e3+r , h1   , 0, Lc2, 10)
factory.addPoint( e1+e2, h1   , 0, Lc1, 11)
factory.addPoint( e1+e2, 0    , 0, Lc1, 12)
factory.addPoint( e2   , 0    , 0, Lc1, 13)

factory.addPoint( R1 / ssin, h5+R1*ccos, 0, Lc2, 14)
factory.addPoint( 0        , h5        , 0, Lc2, 15)
factory.addPoint(-R1 / ssin, h5+R1*ccos, 0, Lc2, 16)
factory.addPoint(-e2       , 0.0       , 0, Lc1, 17)

factory.addPoint(-R2 , h1+h3   , 0, Lc2, 18)
factory.addPoint(-R2 , h1+h3+h4, 0, Lc2, 19)
factory.addPoint( 0  , h1+h3+h4, 0, Lc2, 20)
factory.addPoint( R2 , h1+h3+h4, 0, Lc2, 21)
factory.addPoint( R2 , h1+h3   , 0, Lc2, 22)
factory.addPoint( 0  , h1+h3   , 0, Lc2, 23)

factory.addPoint( 0, h1+h3+h4+R2, 0, Lc2, 24)
factory.addPoint( 0, h1+h3-R2,    0, Lc2, 25)

factory.addLine(1 , 17, 1)
factory.addLine(17, 16, 2)

factory.addCircleArc(14,15,16, 3)
factory.addLine(14,13, 4)
factory.addLine(13,12, 5)
factory.addLine(12,11, 6)
factory.addLine(11,10, 7)
factory.addCircleArc(8,9,10, 8)
factory.addLine(8,7, 9)
factory.addLine(7,6, 10)
factory.addLine(6,5, 11)
factory.addCircleArc(3,4,5, 12)
factory.addLine(3,2, 13)
factory.addLine(2,1, 14)
factory.addLine(18,19, 15)
factory.addCircleArc(21,20,24, 16)
factory.addCircleArc(24,20,19, 17)
factory.addCircleArc(18,23,25, 18)
factory.addCircleArc(25,23,22, 19)
factory.addLine(21,22, 20)

factory.addCurveLoop([17,-15,18,19,-20,16], 21)
factory.addPlaneSurface([21], 22)
factory.addCurveLoop([11,-12,13,14,1,2,-3,4,5,6,7,-8,9,10], 23)

factory.addPlaneSurface([23,21], 24)

factory.synchronize()

v = gmsh.view.add("comments")

gmsh.view.addListDataString(v, [10, -10], ["Created with Gmsh"])

gmsh.view.addListDataString(v, [0, 0.11, 0], ["Hole"],
                            ["Align", "Center", "Font", "Helvetica"])

gmsh.view.addListDataString(v, [0, 0.09, 0], ["file://../t4_image.png@0.01x0"],
                            ["Align", "Center"])

gmsh.view.addListDataString(v, [-0.01, 0.09, 0],
                            ["file://../t4_image.png@0.01x0,0,0,1,0,1,0"])

gmsh.view.addListDataString(v, [0, 0.12, 0],
                            ["file://../t4_image.png@0.01x0#"],
                            ["Align", "Center"])

gmsh.view.addListDataString(v, [150, -7], ["file://../t4_image.png@20x0"])

gmsh.view.option.setString(v, "DoubleClickedCommand",
                           "Printf('View[0] has been double-clicked!');")
gmsh.option.setString(
    "Geometry.DoubleClickedLineCommand",
    "Printf('Curve %g has been double-clicked!', Geometry.DoubleClickedEntityTag);")

gmsh.model.setColor([(2, 22)], 127, 127, 127)
gmsh.model.setColor([(2, 24)], 160, 32, 240)
gmsh.model.setColor([(1, i) for i in 1:14], 255, 0, 0)
gmsh.model.setColor([(1, i) for i in 15:20], 255, 255, 0)

gmsh.model.mesh.generate(2)

gmsh.write("t4.msh")

if !("-nopopup" in ARGS)
    gmsh.fltk.run()
end

gmsh.finalize()
