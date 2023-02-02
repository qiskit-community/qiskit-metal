/*********************************************************************
 *
 *  Gmsh tutorial
 *
 *  Homology and cohomology computation
 *
 *********************************************************************/

// Homology computation in Gmsh finds representative chains of
// (relative) (co)homology space bases using a mesh of a model.
// The representative basis chains are stored in the mesh as
// physical groups of Gmsh, one for each chain.

// Create an example geometry

m=0.5; // mesh size
h=2;

Point(newp) = {0, 0, 0, m};
Point(newp) = {10, 0, 0, m};
Point(newp) = {10, 10, 0, m};
Point(newp) = {0, 10, 0, m};
Point(newp) = {4, 4, 0, m};
Point(newp) = {6, 4, 0, m};
Point(newp) = {6, 6, 0, m};
Point(newp) = {4, 6, 0, m};

Point(newp) = {2, 0, 0, m};
Point(newp) = {8, 0, 0, m};
Point(newp) = {2, 10, 0, m};
Point(newp) = {8, 10, 0, m};

Point(newp) = {0, 0, h, m};
Point(newp) = {10, 0, h, m};
Point(newp) = {10, 10, h, m};
Point(newp) = {0, 10, h, m};
Point(newp) = {4, 4, h, m};
Point(newp) = {6, 4, h, m};
Point(newp) = {6, 6, h, m};
Point(newp) = {4, 6, h, m};

Point(newp) = {2, 0, h, m};
Point(newp) = {8, 0, h, m};
Point(newp) = {2, 10, h, m};
Point(newp) = {8, 10, h, m};
Line(1) = {16, 23};
Line(2) = {23, 11};
Line(3) = {11, 4};
Line(4) = {4, 16};
Line(5) = {24, 12};
Line(6) = {12, 3};
Line(7) = {3, 15};
Line(8) = {15, 24};
Line(9) = {10, 2};
Line(10) = {2, 14};
Line(11) = {14, 22};
Line(12) = {22, 10};
Line(13) = {21, 9};
Line(14) = {9, 1};
Line(15) = {1, 13};
Line(16) = {13, 21};
Curve Loop(17) = {3, 4, 1, 2};
Surface(18) = {17};
Curve Loop(19) = {6, 7, 8, 5};
Surface(20) = {19};
Curve Loop(21) = {9, 10, 11, 12};
Surface(22) = {21};
Curve Loop(23) = {14, 15, 16, 13};
Surface(24) = {23};
Line(25) = {16, 13};
Line(26) = {1, 4};
Line(27) = {11, 12};
Line(28) = {24, 23};
Line(29) = {21, 22};
Line(30) = {10, 9};
Line(31) = {2, 3};
Line(32) = {15, 14};
Line(33) = {20, 19};
Line(34) = {19, 18};
Line(35) = {18, 17};
Line(36) = {17, 20};
Line(37) = {8, 7};
Line(38) = {7, 6};
Line(39) = {6, 18};
Line(40) = {5, 6};
Line(41) = {5, 8};
Line(42) = {20, 8};
Line(43) = {17, 5};
Line(44) = {19, 7};
Curve Loop(45) = {27, -5, 28, 2};
Surface(46) = {45};
Curve Loop(47) = {25, -15, 26, 4};
Surface(48) = {47};
Curve Loop(49) = {29, 12, 30, -13};
Surface(50) = {49};
Curve Loop(51) = {32, -10, 31, 7};
Surface(52) = {51};
Curve Loop(53) = {41, -42, -36, 43};
Surface(54) = {53};
Curve Loop(55) = {35, 43, 40, 39};
Surface(56) = {55};
Curve Loop(57) = {34, -39, -38, -44};
Surface(58) = {57};
Curve Loop(59) = {33, 44, -37, -42};
Surface(60) = {59};
Curve Loop(61) = {27, 6, -31, -9, 30, 14, 26, -3};
Curve Loop(62) = {37, 38, -40, 41};
Plane Surface(63) = {61, 62};
Curve Loop(64) = {25, 16, 29, -11, -32, 8, 28, -1};
Curve Loop(65) = {34, 35, 36, 33};
Plane Surface(66) = {64, 65};
Surface Loop(67) = {46, 63, 20, 52, 66, 48, 24, 50, 22, 18, 60, 58, 56, 54};
Volume(68) = {67};

// Create physical groups, which are used to define the domain of the
// homology computation and the subdomain of the relative homology
// computation.

// Whole domain
Physical Volume(69) = {68};
// Four "terminals" of the model
Physical Surface(70) = {18};
Physical Surface(71) = {20};
Physical Surface(72) = {22};
Physical Surface(73) = {24};
// Whole domain surface
Physical Surface(74) = {46, 18, 20, 52, 22, 50, 24, 48, 66, 63, 60, 58, 56, 54};
// Complement of the domain surface respect to the four terminals
Physical Surface(75) = {46, 63, 66, 52, 50, 48, 54, 60, 58, 56};


// Find bases for relative homology spaces of
// the domain modulo the four terminals.
Homology {{69}, {70, 71, 72, 73}};

// Find homology space bases isomorphic to the previous bases:
// homology spaces modulo the non-terminal domain surface,
// a.k.a the thin cuts.
Homology {{69}, {75}};

// Find cohomology space bases isomorphic to the previous bases:
// cohomology spaces of the domain modulo the four terminals,
// a.k.a the thick cuts.
Cohomology {{69}, {70, 71, 72, 73}};

// More examples (uncomment):
//  Homology = {{69}, {}};
//  Homology {{69}, {74}};
//  Homology {{74}, {70, 71, 72, 73}};
