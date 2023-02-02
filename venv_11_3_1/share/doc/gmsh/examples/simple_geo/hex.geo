DefineConstant[ N = {4, Name "Number of elements per edge"} ];

// example of a purely hexahedral mesh using transfinite constraints and/or
// extrusion

Point(1) = {-2,0,0};
Point(2) = {-1,0,0};
Point(3) = {-1,1,0};
Point(4) = {-2,1,0};
Point(5) = {-2,0,1};
Point(6) = {-1,0,1};
Point(7) = {-1,1,1};
Point(8) = {-2,1,1};
Line(1) = {4,3};
Line(2) = {3,2};
Line(3) = {2,1};
Line(4) = {1,4};
Line(6) = {5,6};
Line(7) = {6,7};
Line(8) = {7,8};
Line(9) = {8,5};
Line(10) = {1,5};
Line(11) = {4,8};
Line(12) = {2,6};
Line(13) = {3,7};
Curve Loop(14) = {3,4,1,2};
Plane Surface(15) = {14};
Curve Loop(16) = {6,7,8,9};
Plane Surface(17) = {16};
Curve Loop(18) = {10,-9,-11,-4};
Plane Surface(19) = {18};
Curve Loop(20) = {8,-11,1,13};
Plane Surface(21) = {20};
Curve Loop(22) = {12,7,-13,2};
Plane Surface(23) = {22};
Curve Loop(24) = {6,-12,3,10};
Plane Surface(25) = {24};
Surface Loop(1) = {17,-25,-23,-21,19,15};
Volume(1) = {1};
/*
By hand:
Transfinite Curve{1:4,6:13} = N+1;
Transfinite Surface {15} = {1,2,3,4};
Transfinite Surface {17} = {5,6,7,8};
Transfinite Surface {19} = {1,5,8,4};
Transfinite Surface {21} = {4,8,7,3};
Transfinite Surface {23} = {2,6,7,3};
Transfinite Surface {25} = {1,5,6,2};
Transfinite Volume{1} = {1,2,3,4,5,6,7,8};

Or automatically:
*/
Transfinite Curve {:} = N+1;
Transfinite Surface {:};
Transfinite Volume {:};
Recombine Surface {:};

// the same by extruding a transfinite surface mesh

Point(51) = {0,0,0};
Point(52) = {1,0,0};
Point(53) = {1,1,0};
Point(54) = {0,1,0};
Line(51) = {54,53};
Line(52) = {53,52};
Line(53) = {52,51};
Line(54) = {51,54};
Curve Loop(55) = {52,53,54,51};
Plane Surface(56) = {55};
Transfinite Curve{51:54} = N+1;
Transfinite Surface{56} = {51,52,53,54};
Recombine Surface{56};
Extrude {0,0,1} {
  Surface{56}; Layers{N}; Recombine;
}

// and the same by using only extrusions

Point(100) = {2,0,0};
l[] = Extrude {1,0,0}{
  Point{100}; Layers{N};
};
s[] = Extrude {0,1,0}{
  Curve{l[1]}; Layers{N}; Recombine;
};
Extrude {0,0,1}{
  Surface{s[1]}; Layers{N}; Recombine;
}

// add some labels
If(!PostProcessing.NbViews)
View "Mesh Info" {
  T3(-1.5,1.5,0.5,66574){ "Pure Transfinite" };
  T3(0.5,1.5,0.5,66574){ "Extruded Transfinite" };
  T3(2.5,1.5,0.5,66574){ "Pure Extruded" };
};
EndIf
