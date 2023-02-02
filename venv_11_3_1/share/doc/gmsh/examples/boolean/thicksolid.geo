SetFactory("OpenCASCADE");

Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 0.1;

Box(1) = {0,0,0,1,1,1};
Boundary{ Volume{1}; }
ThickSolid(100) = {1, 0.05, 6};

Delete{ Volume{1}; Surface{6};  }
