// Original author: Patrick Dular

Include "tower.i1" ;

/* Post-Processing meshes */

xBox = 30. ;
yBox = y1a * 1.5 ;
pBox = 20. ;

Point(1002) = { xBox, yBox, 0, pBox} ;
Point(1003) = {-xBox, yBox, 0, pBox} ;
Point(1004) = {-xBox, 0,    0, pBox} ;
Point(1005) = { xBox, 0,    0, pBox} ;

Line(2301) = {1004,1005};
Line(2302) = {1005,1002};
Line(2303) = {1002,1003};
Line(2305) = {1003,1004};

Curve Loop(2307) = {2303,2305,2301,2302};
Plane Surface(2308) = {2307};

Transfinite Curve {2301,2303}  = 61  ;
Transfinite Curve {2302,-2305} = 61 ;
Transfinite Surface {2308} = {1003,1002,1005,1004} ;
Recombine Surface {2308} ;

Physical Surface (1201) = {2308} ;

xBox = 30. ;
zBox = 150. ;
pBox = 20. ;

Point(1006) = { xBox, 1, zBox, pBox} ;
Point(1007) = {-xBox, 1, zBox, pBox} ;
Point(1008) = {-xBox, 1,    0, pBox} ;
Point(1009) = { xBox, 1,    0, pBox} ;

Line(2306) = {1008,1009};
Line(2307) = {1009,1006};
Line(2308) = {1006,1007};
Line(2309) = {1007,1008};

Curve Loop(2310) = {2307,2308,2309,2306};
Plane Surface(2311) = {2310};

Transfinite Curve {2306,2308}  = 61  ;
Transfinite Curve {2307,-2309} = 61 ;
Transfinite Surface {2311} = {1007,1006,1009,1008} ;
Recombine Surface {2311} ;

Physical Surface (1202) = {2311} ;
