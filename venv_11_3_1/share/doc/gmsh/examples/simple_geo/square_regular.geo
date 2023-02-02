
Point(1) = {0, 0, 0};
Point(2) = {1, 0, 0} ;
Point(3) = {1, 1, 0} ;
Point(4) = {0, 1, 0} ;

Line(1) = {1,2} ;
Line(2) = {3,2} ;
Line(3) = {3,4} ;
Line(4) = {4,1} ;

Curve Loop(5) = {4,1,-2,3} ;
Plane Surface(6) = {5} ;

Transfinite Curve{1:4} = 10;
Transfinite Surface{6} Alternate;
Mesh.ElementOrder = 2;
