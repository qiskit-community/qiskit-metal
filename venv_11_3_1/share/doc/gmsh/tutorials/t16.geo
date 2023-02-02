// -----------------------------------------------------------------------------
//
//  Gmsh GEO tutorial 16
//
//  Constructive Solid Geometry, OpenCASCADE geometry kernel
//
// -----------------------------------------------------------------------------

// Instead of constructing a model in a bottom-up fashion with Gmsh's built-in
// geometry kernel, starting with version 3 Gmsh allows you to directly use
// alternative geometry kernels. Here we use the OpenCASCADE kernel:

SetFactory("OpenCASCADE");

// Let's build the same model as in `t5.geo', but using constructive solid
// geometry.

// We first create two cubes:
Box(1) = {0,0,0, 1,1,1};
Box(2) = {0,0,0, 0.5,0.5,0.5};

// We apply a boolean difference to create the "cube minus one eigth" shape:
BooleanDifference(3) = { Volume{1}; Delete; }{ Volume{2}; Delete; };

// Boolean operations with OpenCASCADE always create new entities. Adding
// `Delete' in the arguments allows to automatically delete the original
// entities.

// We then create the five spheres:
x = 0 ; y = 0.75 ; z = 0 ; r = 0.09 ;
For t In {1:5}
  x += 0.166 ;
  z += 0.166 ;
  Sphere(3 + t) = {x,y,z,r};
  Physical Volume(t) = {3 + t};
EndFor

// If we had wanted five empty holes we would have used `BooleanDifference'
// again. Here we want five spherical inclusions, whose mesh should be conformal
// with the mesh of the cube: we thus use `BooleanFragments', which intersects
// all volumes in a conformal manner (without creating duplicate interfaces):
v() = BooleanFragments{ Volume{3}; Delete; }{ Volume{3 + 1 : 3 + 5}; Delete; };

// When the boolean operation leads to simple modifications of entities, and if
// one deletes the original entities with `Delete', Gmsh tries to assign the
// same tag to the new entities. (This behavior is governed by the
// `Geometry.OCCBooleanPreserveNumbering' option.)

// Here the `Physical Volume' definitions made above will thus still work, as
// the five spheres (volumes 4, 5, 6, 7 and 8), which will be deleted by the
// fragment operations, will be recreated identically (albeit with new surfaces)
// with the same tags.

// The tag of the cube will change though, so we need to access it
// programmatically:
Physical Volume(10) = v(#v()-1);

// Creating entities using constructive solid geometry is very powerful, but can
// lead to practical issues for e.g. setting mesh sizes at points, or
// identifying boundaries.

// To identify points or other bounding entities you can take advantage of the
// `PointfsOf' (a special case of the more general `Boundary' command) and the
// `In BoundingBox' commands.
lcar1 = .1;
lcar2 = .0005;
lcar3 = .055;
eps = 1e-3;

// Assign a mesh size to all the points of all the volumes:
MeshSize{ PointsOf{ Volume{:}; } } = lcar1;

// Override this constraint on the points of the five spheres:
MeshSize{ PointsOf{ Volume{3 + 1 : 3 + 5}; } } = lcar3;

// Select the corner point by searching for it geometrically:
p() = Point In BoundingBox{0.5-eps, 0.5-eps, 0.5-eps,
                           0.5+eps, 0.5+eps, 0.5+eps};
MeshSize{ p() } = lcar2;

// Additional examples created with the OpenCASCADE geometry kernel are
// available in `t18.geo', `t19.geo' and `t20.geo', as well as in the
// `examples/boolean' directory.
