// -----------------------------------------------------------------------------
//
//  Gmsh GEO tutorial 12
//
//  Cross-patch meshing with compounds
//
// -----------------------------------------------------------------------------

// "Compound" meshing constraints allow to generate meshes across surface
// boundaries, which can be useful e.g. for imported CAD models (e.g. STEP) with
// undesired small features.

// When a `Compound Curve' or `Compound Surface' meshing constraint is given,
// at mesh generation time Gmsh
//  1. meshes the underlying elementary geometrical entities, individually
//  2. creates a discrete entity that combines all the individual meshes
//  3. computes a discrete parametrization (i.e. a piece-wise linear mapping)
//     on this discrete entity
//  4. meshes the discrete entity using this discrete parametrization instead
//     of the underlying geometrical description of the underlying elementary
//     entities making up the compound
//  5. optionally, reclassifies the mesh elements and nodes on the original
//     entities

// Step 3. above can only be performed if the mesh resulting from the
// combination of the individual meshes can be reparametrized, i.e. if the shape
// is "simple enough". If the shape is not amenable to reparametrization, you
// should create a full mesh of the geometry and first re-classify it to
// generate patches amenable to reparametrization (see `t13.geo').

// The mesh of the individual entities performed in Step 1. should usually be
// finer than the desired final mesh; this can be controlled with the
// `Mesh.CompoundMeshSizeFactor' option.

// The optional reclassification on the underlying elementary entities in Step
// 5. is governed by the `Mesh.CompoundClassify' option.

lc = 0.1;

Point(1) = {0, 0, 0, lc};       Point(2) = {1, 0, 0, lc};
Point(3) = {1, 1, 0.5, lc};     Point(4) = {0, 1, 0.4, lc};
Point(5) = {0.3, 0.2, 0, lc};   Point(6) = {0, 0.01, 0.01, lc};
Point(7) = {0, 0.02, 0.02, lc}; Point(8) = {1, 0.05, 0.02, lc};
Point(9) = {1, 0.32, 0.02, lc};

Line(1) = {1, 2}; Line(2) = {2, 8}; Line(3) = {8, 9};
Line(4) = {9, 3}; Line(5) = {3, 4}; Line(6) = {4, 7};
Line(7) = {7, 6}; Line(8) = {6, 1}; Spline(9) = {7, 5, 9};
Line(10) = {6, 8};

Curve Loop(11) = {5, 6, 9, 4};     Surface(1) = {11};
Curve Loop(13) = {-9, 3, 10, 7}; Surface(5) = {13};
Curve Loop(15) = {-10, 2, 1, 8}; Surface(10) = {15};

// Treat curves 2, 3 and 4 as a single curve when meshing (i.e. mesh across
// points 6 and 7)
Compound Curve{2, 3, 4};

// Idem with curves 6, 7 and 8
Compound Curve{6, 7, 8};

// Treat surfaces 1, 5 and 10 as a single surface when meshing (i.e. mesh across
// curves 9 and 10)
Compound Surface{1, 5, 10};
