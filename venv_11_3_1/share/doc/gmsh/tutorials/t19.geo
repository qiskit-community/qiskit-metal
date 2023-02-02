// -----------------------------------------------------------------------------
//
//  Gmsh GEO tutorial 19
//
//  Thrusections, fillets, pipes, mesh size from curvature
//
// -----------------------------------------------------------------------------

// The OpenCASCADE geometry kernel supports several useful features for solid
// modelling.

SetFactory("OpenCASCADE");

// Volumes can be constructed from (closed) curve loops thanks to the
// `ThruSections' command
Circle(1) = {0,0,0, 0.5};       Curve Loop(1) = 1;
Circle(2) = {0.1,0.05,1, 0.1};  Curve Loop(2) = 2;
Circle(3) = {-0.1,-0.1,2, 0.3}; Curve Loop(3) = 3;
ThruSections(1) = {1:3};

// With `Ruled ThruSections' you can force the use of ruled surfaces:
Circle(11) = {2+0,0,0, 0.5};      Curve Loop(11) = 11;
Circle(12) = {2+0.1,0.05,1, 0.1}; Curve Loop(12) = 12;
Circle(13) = {2-0.1,-0.1,2, 0.3}; Curve Loop(13) = 13;
Ruled ThruSections(11) = {11:13};

// We copy the first volume, and fillet all its edges:
v() = Translate{4, 0, 0} { Duplicata{ Volume{1}; } };
f() = Abs(Boundary{ Volume{v(0)}; });
e() = Unique(Abs(Boundary{ Surface{f()}; }));
Fillet{v(0)}{e()}{0.1}

// OpenCASCADE also allows general extrusions along a smooth path. Let's first
// define a spline curve:
nturns = 1;
npts = 20;
r = 1;
h = 1 * nturns;
For i In {0 : npts - 1}
  theta = i * 2*Pi*nturns/npts;
  Point(1000 + i) = {r * Cos(theta), r * Sin(theta), i * h/npts};
EndFor
Spline(1000) = {1000 : 1000 + npts - 1};

// A wire is like a curve loop, but open:
Wire(1000) = {1000};

// We define the shape we would like to extrude along the spline (a disk):
Disk(1000) = {1,0,0, 0.2};
Rotate {{1, 0, 0}, {0, 0, 0}, Pi/2} { Surface{1000}; }

// We extrude the disk along the spline to create a pipe:
Extrude { Surface{1000}; } Using Wire {1000}

// We delete the source surface, and increase the number of sub-edges for a
// nicer display of the geometry:
Delete{ Surface{1000}; }
Geometry.NumSubEdges = 1000;

// We can activate the calculation of mesh element sizes based on curvature
// (here with a target of 20 elements per 2*Pi radians):
Mesh.MeshSizeFromCurvature = 20;

// We can constraint the min and max element sizes to stay within reasonnable
// values (see `t10.geo' for more details):
Mesh.MeshSizeMin = 0.001;
Mesh.MeshSizeMax = 0.3;
