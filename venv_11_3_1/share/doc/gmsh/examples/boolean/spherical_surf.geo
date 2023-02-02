SetFactory("OpenCASCADE");
R = 1;
R1 = 0.95;
Sphere(1) = {0,0,0, R, 0, Pi/2, Pi/2};
Box(2) = {R1,0,0, R,R,R};
Box(3) = {0,R1,0, R,R,R};
Box(4) = {0,0,R1, R,R,R};
BooleanDifference{ Volume{1}; Delete; }{ Volume{2:4}; Delete; }
Delete{ Volume{1}; }
Recursive Delete{ Surface{2,4,6}; }
