SetFactory("OpenCASCADE");

r = 1;
Sphere(1) = {0,0,0, r};
Sphere(2) = {2,0,0, r};

Mesh.MeshSizeMin = 0.1;
Mesh.MeshSizeMax = 0.1;

// hide volume 2 (to test Plugin(Integrate)'s ability to only integrate on
// what's visible)
Recursive Hide { Volume{2}; }

// mesh
Mesh 3;

// compute post-processing data view with constant value 1 on the mesh
Plugin(NewView).Run;
Plugin(ModifyComponents).View = 0;
Plugin(ModifyComponents).Expression0 = "1";
Plugin(ModifyComponents).Run;

// compute surface of sphere 1
Plugin(Integrate).View = 0;
Plugin(Integrate).Visible = 1; // only integrate on what's visible
Plugin(Integrate).Dimension = 2; // only integrate on 2D elements (triangles)
Plugin(Integrate).Run;
Printf("Area = %g (exact = %g)", View[PostProcessing.NbViews-1].Max, 4*Pi*r^2);

// compute volume of sphere 1
Plugin(Integrate).View = 0;
Plugin(Integrate).Visible = 1; // only integrate on what's visible
Plugin(Integrate).Dimension = 3; // only integrate on 3D elements (tetrahedra)
Plugin(Integrate).Run;
Printf("Volume = %g (exact = %g)", View[PostProcessing.NbViews-1].Max, 4/3*Pi*r^3);
