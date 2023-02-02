// -----------------------------------------------------------------------------
//
//  Gmsh GEO tutorial 18
//
//  Periodic meshes
//
// -----------------------------------------------------------------------------

// Periodic meshing constraints can be imposed on surfaces and curves.

// Let's use the OpenCASCADE geometry kernel to build two geometries.

SetFactory("OpenCASCADE");

// The first geometry is very simple: a unit cube with a non-uniform mesh size
// constraint (set on purpose to be able to verify visually that the periodicity
// constraint works!):

Box(1) = {0, 0, 0, 1, 1, 1};
MeshSize {:} = 0.1;
MeshSize {1} = 0.02;

// To impose that the mesh on surface 2 (the right side of the cube) should
// match the mesh from surface 1 (the left side), the following periodicity
// constraint is set:
Periodic Surface {2} = {1} Translate {1, 0, 0};

// During mesh generation, the mesh on surface 2 will be created by copying the
// mesh from surface 1.  Periodicity constraints can be specified with a
// `Translation', a `Rotation' or a general `Affine' transform.

// Multiple periodicities can be imposed in the same way:
Periodic Surface {6} = {5} Translate {0, 0, 1};
Periodic Surface {4} = {3} Translate {0, 1, 0};

// For more complicated cases, finding the corresponding surfaces by hand can be
// tedious, especially when geometries are created through solid
// modelling. Let's construct a slightly more complicated geometry.

// We start with a cube and some spheres:
Box(10) = {2, 0, 0, 1, 1, 1};
x = 2-0.3; y = 0; z = 0;
Sphere(11) = {x, y, z, 0.35};
Sphere(12) = {x+1, y, z, 0.35};
Sphere(13) = {x, y+1, z, 0.35};
Sphere(14) = {x, y, z+1, 0.35};
Sphere(15) = {x+1, y+1, z, 0.35};
Sphere(16) = {x, y+1, z+1, 0.35};
Sphere(17) = {x+1, y, z+1, 0.35};
Sphere(18) = {x+1, y+1, z+1, 0.35};

// We first fragment all the volumes, which will leave parts of spheres
// protruding outside the cube:
v() = BooleanFragments { Volume{10}; Delete; }{ Volume{11:18}; Delete; };

// Ask OpenCASCADE to compute more accurate bounding boxes of entities using the
// STL mesh:
Geometry.OCCBoundsUseStl = 1;

// We then retrieve all the volumes in the bounding box of the original cube,
// and delete all the parts outside it:
eps = 1e-3;
vin() = Volume In BoundingBox {2-eps,-eps,-eps, 2+1+eps,1+eps,1+eps};
v() -= vin();
Recursive Delete{ Volume{v()}; }

// We now set a non-uniform mesh size constraint (again to check results
// visually):
MeshSize { PointsOf{ Volume{vin()}; }} = 0.1;
p() = Point In BoundingBox{2-eps, -eps, -eps, 2+eps, eps, eps};
MeshSize {p()} = 0.001;

// We now identify corresponding surfaces on the left and right sides of the
// geometry automatically.

// First we get all surfaces on the left:
Sxmin() = Surface In BoundingBox{2-eps, -eps, -eps, 2+eps, 1+eps, 1+eps};

For i In {0:#Sxmin()-1}
  // Then we get the bounding box of each left surface
  bb() = BoundingBox Surface { Sxmin(i) };
  // We translate the bounding box to the right and look for surfaces inside it:
  Sxmax() = Surface In BoundingBox { bb(0)-eps+1, bb(1)-eps, bb(2)-eps,
                                     bb(3)+eps+1, bb(4)+eps, bb(5)+eps };
  // For all the matches, we compare the corresponding bounding boxes...
  For j In {0:#Sxmax()-1}
    bb2() = BoundingBox Surface { Sxmax(j) };
    bb2(0) -= 1;
    bb2(3) -= 1;
    // ...and if they match, we apply the periodicity constraint
    If(Fabs(bb2(0)-bb(0)) < eps && Fabs(bb2(1)-bb(1)) < eps &&
       Fabs(bb2(2)-bb(2)) < eps && Fabs(bb2(3)-bb(3)) < eps &&
       Fabs(bb2(4)-bb(4)) < eps && Fabs(bb2(5)-bb(5)) < eps)
      Periodic Surface {Sxmax(j)} = {Sxmin(i)} Translate {1,0,0};
    EndIf
  EndFor
EndFor
