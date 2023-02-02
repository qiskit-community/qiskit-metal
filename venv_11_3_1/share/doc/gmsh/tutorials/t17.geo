// -----------------------------------------------------------------------------
//
//  Gmsh GEO tutorial 17
//
//  Anisotropic background mesh
//
// -----------------------------------------------------------------------------

// As seen in `t7.geo', mesh sizes can be specified very accurately by providing
// a background mesh, i.e., a post-processing view that contains the target mesh
// sizes.

// Here, the background mesh is represented as a metric tensor field defined on
// a square. One should use bamg as 2d mesh generator to enable anisotropic
// meshes in 2D.

SetFactory("OpenCASCADE");

// Create a square
Rectangle(1) = {-2, -2, 0, 4, 4};

// Merge a post-processing view containing the target anisotropic mesh sizes
Merge "t17_bgmesh.pos";

// Apply the view as the current background mesh
Background Mesh View[0];

// Use bamg
Mesh.SmoothRatio = 3;
Mesh.AnisoMax = 1000;
Mesh.Algorithm = 7;
