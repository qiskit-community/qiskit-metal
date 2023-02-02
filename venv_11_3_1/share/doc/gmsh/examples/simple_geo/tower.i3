
/* INPUT :
   i_p
   i_l
*/

Point(i_p + 0) = { x, y-dy0, z8+z0, p0} ;
Point(i_p + 1) = { x, y-dy1, z8+z1, p0} ;
Point(i_p + 2) = { x, y-dy2, z8+z2, p0} ;
Point(i_p + 3) = { x, y-dy3, z8+z3, p0} ;
Point(i_p + 4) = { x, y-dy4, z8+z4, p0} ;
Point(i_p + 5) = { x, y-dy5, z8+z5, p0} ;
Point(i_p + 6) = { x, y-dy6, z8+z6, p0} ;
Point(i_p + 7) = { x, y-dy7, z8+z7, p0} ;
Point(i_p + 8) = { x, y-dy8, z8+z8, p0} ;

Point(i_p + 11) = { x, y-dy1,z8-z1, p0} ;
Point(i_p + 12) = { x, y-dy2,z8-z2, p0} ;
Point(i_p + 13) = { x, y-dy3,z8-z3, p0} ;
Point(i_p + 14) = { x, y-dy4,z8-z4, p0} ;
Point(i_p + 15) = { x, y-dy5,z8-z5, p0} ;
Point(i_p + 16) = { x, y-dy6,z8-z6, p0} ;
Point(i_p + 17) = { x, y-dy7,z8-z7, p0} ;
Point(i_p + 18) = { x, y-dy8,z8-z8, p0} ;


Point(i_p + 20) = { x, y-dy0, -z8+z0, p0} ;
Point(i_p + 21) = { x, y-dy1, -z8+z1, p0} ;
Point(i_p + 22) = { x, y-dy2, -z8+z2, p0} ;
Point(i_p + 23) = { x, y-dy3, -z8+z3, p0} ;
Point(i_p + 24) = { x, y-dy4, -z8+z4, p0} ;
Point(i_p + 25) = { x, y-dy5, -z8+z5, p0} ;
Point(i_p + 26) = { x, y-dy6, -z8+z6, p0} ;
Point(i_p + 27) = { x, y-dy7, -z8+z7, p0} ;


Spline(i_l + 0) = {i_p, i_p+1 : i_p+8};
Spline(i_l + 1) = {i_p, i_p+11 : i_p+18};
Spline(i_l + 2) = {i_p+20 : i_p+27, i_p + 18};

