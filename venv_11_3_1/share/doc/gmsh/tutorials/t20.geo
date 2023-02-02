// -----------------------------------------------------------------------------
//
//  Gmsh GEO tutorial 20
//
//  STEP import and manipulation, geometry partitioning
//
// -----------------------------------------------------------------------------

// The OpenCASCADE geometry kernel allows to import STEP files and to modify
// them. In this tutorial we will load a STEP geometry and partition it into
// slices.

SetFactory("OpenCASCADE");

// Load a STEP file (using `ShapeFromFile' instead of `Merge' allows to directly
// retrieve the tags of the highest dimensional imported entities):
v() = ShapeFromFile("t20_data.step");

// If we had specified
//
// Geometry.OCCTargetUnit = "M";
//
// before merging the STEP file, OpenCASCADE would have converted the units to
// meters (instead of the default, which is millimeters).

// Get the bounding box of the volume:
bbox() = BoundingBox Volume{v()};
xmin = bbox(0);
ymin = bbox(1);
zmin = bbox(2);
xmax = bbox(3);
ymax = bbox(4);
zmax = bbox(5);

// We want to slice the model into N slices, and either keep the volume slices
// or just the surfaces obtained by the cutting:
DefineConstant[
  N = {5, Min 2, Max 100, Step 1, Name "Parameters/0Number of slices"}
  dir = {0, Choices{0="X", 1="Y", 2="Z"}, Name "Parameters/1Direction"}
  surf = {0, Choices{0, 1}, Name "Parameters/2Keep only surfaces?"}
];

dx = (xmax - xmin);
dy = (ymax - ymin);
dz = (zmax - zmin);
L = (dir == 0) ? dz : dx;
H = (dir == 1) ? dz : dy;

// Create the first cutting plane:
s() = {news};
Rectangle(s(0)) = {xmin, ymin, zmin, L, H};
If(dir == 0)
  Rotate{ {0, 1, 0}, {xmin, ymin, zmin}, -Pi/2 } { Surface{s(0)}; }
ElseIf(dir == 1)
  Rotate{ {1, 0, 0}, {xmin, ymin, zmin}, Pi/2 } { Surface{s(0)}; }
EndIf
tx = (dir == 0) ? dx / N : 0;
ty = (dir == 1) ? dy / N : 0;
tz = (dir == 2) ? dz / N : 0;
Translate{tx, ty, tz} { Surface{s(0)}; }

// Create the other cutting planes:
For i In {1:N-2}
  s() += Translate{i * tx, i * ty, i * tz} { Duplicata{ Surface{s(0)}; } };
EndFor

// Fragment (i.e. intersect) the volume with all the cutting planes:
BooleanFragments{ Volume{v()}; Delete; }{ Surface{s()}; Delete; }

// Now remove all the surfaces (and their bounding entities) that are not on the
// boundary of a volume, i.e. the parts of the cutting planes that "stick out"
// of the volume:
Recursive Delete { Surface{:}; }

If(surf)
  // If we want to only keep the surfaces, retrieve the surfaces in bounding
  // boxes around the cutting planes...
  eps = 1e-4;
  s() = {};
  For i In {1:N-1}
    xx = (dir == 0) ? xmin : xmax;
    yy = (dir == 1) ? ymin : ymax;
    zz = (dir == 2) ? zmin : zmax;
    s() += Surface In BoundingBox
      {xmin - eps + i * tx, ymin - eps + i * ty, zmin - eps + i * tz,
       xx + eps + i * tx, yy + eps + i * ty, zz + eps + i * tz};
  EndFor
  // ...and remove all the other entities:
  dels = Surface{:};
  dels -= s();
  Delete { Volume{:}; Surface{dels()}; Curve{:}; Point{:}; }
EndIf

// Finally, let's specify a global mesh size:
Mesh.MeshSizeMin = 3;
Mesh.MeshSizeMax = 3;

// To partition the mesh instead of the geometry, see `t21.geo'.
