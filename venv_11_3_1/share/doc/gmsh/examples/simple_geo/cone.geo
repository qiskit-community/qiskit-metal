lc = 0.2;
Point(1) = {0,0,0,lc};
Point(2) = {1,0,0,lc};
Point(6) = {0,0,3,lc};
Line(1) = {1,2};
Line(2) = {2,6};
Line(3) = {6,1};
Curve Loop(4) = {2,3,1};
Plane Surface(5) = {4};
Extrude {{0,0,1}, {0,0,0}, Pi/2} { Surface{5}; }
Extrude {{0,0,1}, {0,0,0}, Pi/2} { Surface{17}; }
Extrude {{0,0,1}, {0,0,0}, Pi/2} { Surface{29}; }
Extrude {{0,0,1}, {0,0,0}, Pi/2} { Surface{41}; }
