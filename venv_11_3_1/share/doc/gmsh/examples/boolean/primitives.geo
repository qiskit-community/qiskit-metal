SetFactory("OpenCASCADE");

//Mesh.Algorithm = 6;
Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 0.1;

// 3D
x = 0; y = 0;
Sphere(newv) = {x++,y,0, 0.3};
Sphere(newv) = {x++,y,0, 0.3, Pi/4};
Sphere(newv) = {x++,y,0, 0.3, -Pi/4, Pi/4};
Sphere(newv) = {x++,y,0, 0.3, -Pi/4, Pi/4, Pi/2};
Sphere(newv) = {x++,y,0, 0.3, -Pi/2, Pi/2, Pi/4};
Cylinder(newv) = {x++,y,0, 0.5,0,0, 0.5};
Cylinder(newv) = {x++,y,0, 0.5,0,0, 0.5, Pi/3};
Box(newv) = {x++,y,0, 0.5,0.5,0.5};
Torus(newv) = {x++,y,0, 0.3, 0.1};
Torus(newv) = {x++,y,0, 0.3, 0.1, Pi/3};
Cone(newv) = {x++,y,0, 0.5,0,0, 0.5,0};
Cone(newv) = {x++,y,0, 0.5,0,0, 0.5,0, Pi/3};
Cone(newv) = {x++,y,0, 0.5,0,0, 0.5,0.2, Pi/3};
Wedge(newv) = {x++,y,0, 0.5,0.5,0.5};
Wedge(newv) = {x++,y,0, 0.5,0.5,0.5, 0.8};

// 2D
x = 0; y = -1.5;
Rectangle(news) = {x++,y,0, 0.5,0.5};
Rectangle(news) = {x++,y,0, 0.5,0.5, 0.1};
Disk(news) = {x++,y,0, 0.3};
Disk(news) = {x++,y,0, 0.4,0.2};

p = newp;
  Point(p) = {x++,y,0}; Point(p+1) = {x-0.7,y+0.5,0}; Point(p+2) = {x-0.3,y+0.5,0};
  Point(p+3) = {x-0.1,y,0}; Point(p+4) = {x-0.9,y-0.2,0};
l = newl;
  Bezier(l) = {p,p+4,p+3,p+2}; Line(l+1) = {p+2,p+1}; Line(l+2) = {p+1,p};
ll = newll;
  Curve Loop(ll) = {l:l+2};
Plane Surface(news) = {ll};

l = newl; Circle(l) = {x++,y,0, 0.3}; Circle(l+1) = {x-1,y-0.1,0, 0.1};
ll = newll; Curve Loop(ll) = l; Curve Loop(ll+1) = l+1;
Plane Surface(news) = {ll, ll+1};

p = newp;
  Point(p) = {x++,y,0.3}; Point(p+1) = {x-0.7,y+0.5,0}; Point(p+2) = {x-0.3,y+0.5,0};
  Point(p+3) = {x-0.1,y,0}; Point(p+4) = {x-0.9,y-0.2,0};
l = newl;
  Bezier(l) = {p,p+4,p+3,p+2}; Line(l+1) = {p+2,p+1}; Line(l+2) = {p+1,p};
ll = newll;
  Curve Loop(ll) = {l:l+2};
Surface(news) = {ll};

// 1D
x = 0; y = -3;
p = newp; Point(p) = {x++,y,0}; Point(p+1) = {x-0.5,y,0};
Line(newl) = {p,p+1};

p = newp; Point(p) = {x++,y,0}; Point(p+1) = {x-0.5,y,0}; Point(p+2) = {x-1,y+0.5,0};
Circle(newl) = {p+1,p,p+2};
Circle(newl) = {x++,y,0, 0.3};
Circle(newl) = {x++,y,0, 0.3, Pi/3};
Circle(newl) = {x++,y,0, 0.3, -Pi/3, Pi/3};

p = newp; Point(p) = {x++,y,0}; Point(p+1) = {x-0.5,y,0}; Point(p+2) = {x-1,y+0.2,0};
Ellipse(newl) = {p+1,p,p+1,p+2};
Ellipse(newl) = {x++,y,0, 0.4,0.1};
Ellipse(newl) = {x++,y,0, 0.4,0.1, Pi/3};
Ellipse(newl) = {x++,y,0, 0.4,0.1, -Pi/3, Pi/3};

p = newp; Point(p) = {x++,y,0}; Point(p+1) = {x-0.5,y+0.3,0}; Point(p+2) = {x-0.2,y,0};
Spline(newl) = {p:p+2};

p = newp; Point(p) = {x++,y,0}; Point(p+1) = {x-0.5,y+0.3,0}; Point(p+2) = {x-0.2,y,0};
Bezier(newl) = {p:p+2};

// 0D
x = 0; y = -4.5;
Point(newp) = {x++,y,0};
