// -----------------------------------------------------------------------------
//
//  Gmsh GEO tutorial 11
//
//  Unstructured quadrangular meshes
//
// -----------------------------------------------------------------------------

// We have seen in tutorials `t3.geo' and `t6.geo' that extruded and transfinite
// meshes can be "recombined" into quads, prisms or hexahedra by using the
// "Recombine" keyword. Unstructured meshes can be recombined in the same
// way. Let's define a simple geometry with an analytical mesh size field:

Point(1) = {-1.25, -.5, 0}; Point(2) = {1.25, -.5, 0};
Point(3) = {1.25, 1.25, 0};  Point(4) = {-1.25, 1.25, 0};

Line(1) = {1, 2}; Line(2) = {2, 3};
Line(3) = {3, 4}; Line(4) = {4, 1};

Curve Loop(4) = {1, 2, 3, 4}; Plane Surface(100) = {4};

Field[1] = MathEval;
Field[1].F = "0.01*(1.0+30.*(y-x*x)*(y-x*x) + (1-x)*(1-x))";
Background Field = 1;

// To generate quadrangles instead of triangles, we can simply add

Recombine Surface{100};

// If we'd had several surfaces, we could have used `Recombine Surface {:};'.
// Yet another way would be to specify the global option "Mesh.RecombineAll =
// 1;".

// The default recombination algorithm is called "Blossom": it uses a minimum
// cost perfect matching algorithm to generate fully quadrilateral meshes from
// triangulations. More details about the algorithm can be found in the
// following paper: J.-F. Remacle, J. Lambrechts, B. Seny, E. Marchandise,
// A. Johnen and C. Geuzaine, "Blossom-Quad: a non-uniform quadrilateral mesh
// generator using a minimum cost perfect matching algorithm", International
// Journal for Numerical Methods in Engineering 89, pp. 1102-1119, 2012.

// For even better 2D (planar) quadrilateral meshes, you can try the
// experimental "Frontal-Delaunay for quads" meshing algorithm, which is a
// triangulation algorithm that enables to create right triangles almost
// everywhere: J.-F. Remacle, F. Henrotte, T. Carrier-Baudouin, E. Bechet,
// E. Marchandise, C. Geuzaine and T. Mouton. A frontal Delaunay quad mesh
// generator using the L^inf norm. International Journal for Numerical Methods
// in Engineering, 94, pp. 494-512, 2013. Uncomment the following line to try
// the Frontal-Delaunay algorithms for quads:
//
// Mesh.Algorithm = 8;

// The default recombination algorithm might leave some triangles in the mesh,
// if recombining all the triangles leads to badly shaped quads. In such cases,
// to generate full-quad meshes, you can either subdivide the resulting hybrid
// mesh (with Mesh.SubdivisionAlgorithm = 1), or use the full-quad recombination
// algorithm, which will automatically perform a coarser mesh followed by
// recombination, smoothing and subdivision. Uncomment the following line to try
// the full-quad algorithm:
//
// Mesh.RecombinationAlgorithm = 2; // or 3

// Note that you could also apply the recombination algorithm and/or the
// subdivision step explicitly after meshing, as follows:
//
// Mesh 2;
// RecombineMesh;
// Mesh.SubdivisionAlgorithm = 1;
// RefineMesh;
