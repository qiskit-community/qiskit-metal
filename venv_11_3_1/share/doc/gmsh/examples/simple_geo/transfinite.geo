l = 1;
r1 = 2;
r2 = 0.5;
n = 10;
n2 = n;
progr = 2;

// exterior cube
Point(1) = {0,0,0,l};
Point(2) = {r1,r1,-r1,l};
Point(3) = {-r1,r1,-r1,l};
Point(4) = {-r1,-r1,-r1,l};
Point(5) = {r1,-r1,-r1,l};
Line(1) = {2,3};
Line(2) = {3,4};
Line(3) = {4,5};
Line(4) = {5,2};
Curve Loop(5) = {4,1,2,3};
Plane Surface(6) = {5};
Extrude {0.0,0.0,2*r1}{ Surface {6}; }
Delete { Volume{1}; }

// interior sphere
Point(102) = {r2,r2,-r2,l};
Point(103) = {-r2,r2,-r2,l};
Point(104) = {-r2,-r2,-r2,l};
Point(105) = {r2,-r2,-r2,l};
Circle(29) = {103,1,102};
Circle(30) = {102,1,105};
Circle(31) = {105,1,104};
Circle(32) = {104,1,103};
Curve Loop(33) = {29,30,31,32};
Surface(34) = {33};
Rotate { {1,0,0},{0,0,0}, Pi/2 } { Duplicata{ Surface{34}; } }
Rotate { {1,0,0},{0,0,0}, Pi } { Duplicata{ Surface{34}; } }
Rotate { {1,0,0},{0,0,0}, 3*Pi/2 } { Duplicata{ Surface{34}; } }
Rotate { {0,1,0},{0,0,0}, Pi/2 } { Duplicata { Surface{34}; } }
Rotate { {0,1,0},{0,0,0}, -Pi/2 } { Duplicata { Surface{34}; } }

// connect sphere and cube
Line(52) = {102,2};
Line(53) = {108,7};
Line(54) = {105,5};
Line(55) = {111,6};
Line(56) = {109,15};
Line(57) = {104,4};
Line(58) = {103,3};
Line(59) = {106,11};

Curve Loop(60) = {58,-1,-52,-29};Plane Surface(61) = {60};
Curve Loop(62) = {58,18,-59,-39};Plane Surface(63) = {62};
Curve Loop(64) = {59,-9,-53,-36};Plane Surface(65) = {64};
Curve Loop(66) = {37,52,14,-53};Plane Surface(67) = {66};
Curve Loop(68) = {56,-22,-57,-49};Plane Surface(69) = {68};
Curve Loop(70) = {31,57,3,-54};Plane Surface(71) = {70};
Curve Loop(72) = {54,13,-55,-47};Plane Surface(73) = {72};
Curve Loop(74) = {55,-11,-56,41};Plane Surface(75) = {74};
Curve Loop(76) = {59,10,-56,-44};Plane Surface(77) = {76};
Curve Loop(78) = {58,2,-57,32};Plane Surface(79) = {78};
Curve Loop(80) = {52,-4,-54,-30};Plane Surface(81) = {80};
Curve Loop(82) = {42,53,-8,-55};Plane Surface(83) = {82};

// connection volumes
Surface Loop(84) = {19,61,-63,-65,67,-35}; Volume(85) = {84};
Surface Loop(86) = {34,61,-79,6,81,-71}; Volume(87) = {86};
Surface Loop(88) = {23,-79,63,77,69,-50}; Volume(89) = {88};
Surface Loop(90) = {28,83,-40,75,-77,65}; Volume(91) = {90};
Surface Loop(92) = {15,81,-67,-51,-83,73}; Volume(93) = {92};
Surface Loop(94) = {27,-71,-45,-73,-75,-69}; Volume(95) = {94};

// define transfinite mesh
Transfinite Curve {53, 59, 52, 58, 55, 56, 54, 57} = n Using Progression progr;
Transfinite Curve {42, 44, 30, 32, 36, 41, 29, 31, 9, 1, 8, 4, 11, 3, 10, 2,
                  18, 22, 14, 13, 39, 49, 37, 47} = n2;
Transfinite Surface {:};
Recombine Surface {:};
Transfinite Volume {:};

/* Here's a way to apply these constraints in a more generic manner, e.g.
   on an imported geometry,

s() = Surface{:};
For i In {0:#s()-1}
  c() = Boundary { Surface{s(i)}; };
  If(#c() == 4)
    Transfinite Curve{c()} = n;
    Transfinite Surface{s(i)};
    Recombine Surface{s(i)};
  EndIf
EndFor

v() = Volume{:};
For i In {0:#v()-1}
  s() = Boundary { Volume{v(i)}; };
  If(#s() == 6)
    Transfinite Volume{v(i)};
  EndIf
EndFor
*/

Physical Volume(1) = {85:95:2}; // ext volume
Physical Surface(100) = {34,35,40,45,50,51}; // int surf
Physical Surface(101) = {6,15,19,23,27,28}; // ext surf
