SetFactory("OpenCASCADE");

//Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 0.02;
Mesh.MeshSizeMax = 0.02;
Point(1) = {-0.8, 0.1, -0.2, 1.0};
Point(2) = {-0.5, 0.1, -0.2, 1.0};
Point(3) = {-0.6, 0, -0.1, 1.0};
Point(4) = {-0.7, -0, -0.1, 1.0};
Point(5) = {-0.7, 0.2, -0.2, 1.0};
Point(6) = {-0.6, 0.1, -0.1, 1.0};
Spline(1) = {1, 5, 2};
Spline(2) = {2, 6, 3};
Spline(3) = {3, 4, 1};
Curve Loop(1) = {1, 2, 3};

// Bspline surface bounded by curve loop 1, constructed by optimization
Surface(1) = {1};

// BSpline filling
BSpline Surface(2) = {1};

// Bezier filling - can be used if all bounding curves are Bezier curves
// Bezier Surface(3) = {1};

Point(7) = {-0.7, 0.1, -0.2, 1.0};
Point(8) = {-0.67, 0.1, -0.2, 1.0};
// Same as 1, but passing through points 7 and 8
Surface(4) = {1} Using Point {7,8};
