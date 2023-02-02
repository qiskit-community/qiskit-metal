SetFactory("OpenCASCADE");

Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 1;
Mesh.MeshSizeMax = 1;

For i In {1:10}
  Point(i) = {i, Sin(i/9*2*Pi), 0};
EndFor
Line(1) = {1,10};
Bezier(2) = {1:10};
Spline(3) = {1:10};
BSpline(4) = {1:10};


Point(101) = {0.2,-1.6,0,0.1};
Point(102) = {1.2,-1.6,0,0.1};
Point(103) = {1.2,-1.1,0,0.1};
Point(104) = {0.3,-1.1,0,0.1};
Point(105) = {0.7,-1,0,0.1};

// periodic bspline (C2) through the control points
Spline(100) = {103,102,101,104,105,103};
Curve Loop(100) = {100};
Plane Surface(100) = {100};

// periodic bspline with given control points and default parameters (order 3,
// C2)
BSpline(101) = {103,102,101,104,105,103};


// general bspline
Point(201) = {0,-2,0,0.1};
Point(202) = {1,-2,0,0.1};
Point(203) = {1,-3,0,0.1};
Point(204) = {0,-3,0,0.1};
Nurbs(201) = {201,202,203,204} Knots {0,0,0, 0.5, 1,1,1} Order 2;
