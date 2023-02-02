// -----------------------------------------------------------------------------
//
//  Gmsh GEO tutorial 6
//
//  Transfinite meshes
//
// -----------------------------------------------------------------------------

// Let's use the geometry from the first tutorial as a basis for this one:
Include "t1.geo";

// Delete the surface and the left line, and replace the line with 3 new ones:
Delete{ Surface{1}; Curve{4}; }

p1 = newp; Point(p1) = {-0.05, 0.05, 0, lc};
p2 = newp; Point(p2) = {-0.05, 0.1, 0, lc};

l1 = newc; Line(l1) = {1, p1};
l2 = newc; Line(l2) = {p1, p2};
l3 = newc; Line(l3) = {p2, 4};

// Create a surface:
Curve Loop(2) = {2, -1, l1, l2, l3, -3};
Plane Surface(1) = {-2};

// The `Transfinite Curve' meshing constraints explicitly specifies the location
// of the nodes on the curve. For example, the following command forces 20
// uniformly placed nodes on curve 2 (including the nodes on the two end
// points):
Transfinite Curve{2} = 20;

// Let's put 20 points total on combination of curves `l1', `l2' and `l3'
// (beware that the points `p1' and `p2' are shared by the curves, so we do not
// create 6 + 6 + 10 = 22 nodes, but 20!)
Transfinite Curve{l1} = 6;
Transfinite Curve{l2} = 6;
Transfinite Curve{l3} = 10;

// Finally, we put 30 nodes following a geometric progression on curve 1
// (reversed) and on curve 3:
Transfinite Curve{-1, 3} = 30 Using Progression 1.2;

// The `Transfinite Surface' meshing constraint uses a transfinite interpolation
// algorithm in the parametric plane of the surface to connect the nodes on the
// boundary using a structured grid. If the surface has more than 4 corner
// points, the corners of the transfinite interpolation have to be specified by
// hand:
Transfinite Surface{1} = {1, 2, 3, 4};

// To create quadrangles instead of triangles, one can use the `Recombine'
// command:
Recombine Surface{1};

// When the surface has only 3 or 4 points on its boundary the list of corners
// can be omitted in the `Transfinite Surface' constraint:
Point(7) = {0.2, 0.2, 0, 1.0};
Point(8) = {0.2, 0.1, 0, 1.0};
Point(9) = {-0, 0.3, 0, 1.0};
Point(10) = {0.25, 0.2, 0, 1.0};
Point(11) = {0.3, 0.1, 0, 1.0};
Line(10) = {8, 11};
Line(11) = {11, 10};
Line(12) = {10, 7};
Line(13) = {7, 8};
Curve Loop(14) = {13, 10, 11, 12};
Plane Surface(15) = {14};
Transfinite Curve {10:13} = 10;
Transfinite Surface{15};

// The way triangles are generated can be controlled by appending "Left",
// "Right" or "Alternate" after the `Transfinite Surface' command. Try e.g.
//
// Transfinite Surface{15} Alternate;

// Finally we apply an elliptic smoother to the grid to have a more regular
// mesh:
Mesh.Smoothing = 100;
