// -----------------------------------------------------------------------------
//
//  Gmsh C tutorial 1
//
//  Geometry basics, elementary entities, physical groups
//
// -----------------------------------------------------------------------------

#include <string.h>

/* The Gmsh C API is entirely defined in the `gmshc.h' header (which contains
   the full documentation of all the functions in the API): */
#include <gmshc.h>

int main(int argc, char **argv)
{
  // Before using any functions in the C API, Gmsh must be initialized. In the C
  // API the last argument of all functions returns the error code, if any.
  int ierr;
  gmshInitialize(argc, argv, 1, 0, &ierr);

  // We now add a new model, named "t1". If gmsh::model::add() is not called, a
  // new default (unnamed) model will be created on the fly, if necessary.
  gmshModelAdd("t1", &ierr);

  // The C API provides direct access to each supported geometry (CAD)
  // kernel. The built-in kernel is used in this first tutorial: the
  // corresponding API functions have the "gmshModelGeo" prefix.

  // The first type of `elementary entity' in Gmsh is a `Point'. To create a
  // point with the built-in CAD kernel, the C API function is
  // gmshModelGeoAddPoint():
  // - the first 3 arguments are the point coordinates (x, y, z)
  // - the next argument is the target mesh size close to the point
  // - the next argument is the point tag (a stricly positive integer that
  //   uniquely identifies the point); if the tag is set to -1, the function
  //   will return a new tag */
  const double lc = 1e-2;
  gmshModelGeoAddPoint(0, 0, 0, lc, 1, &ierr);

  // The distribution of the mesh element sizes will be obtained by
  // interpolation of these mesh sizes throughout the geometry. Another method
  // to specify mesh sizes is to use general mesh size Fields. A particular case
  // is the use of a background mesh.
  //
  // If no target mesh size of provided, a default uniform coarse size will be
  // used for the model, based on the overall model size.
  //
  // We can then define some additional points. All points should have different
  // tags:
  gmshModelGeoAddPoint(.1, 0,  0, lc, 2, &ierr);
  gmshModelGeoAddPoint(.1, .3, 0, lc, 3, &ierr);

  // If the tag is not provided explicitly (by passing a negative value), a new
  // tag is automatically created, and returned by the function:
  int p4 = gmshModelGeoAddPoint(0,  .3, 0, lc, -1, &ierr);

  // Curves are Gmsh's second type of elementery entities, and, amongst curves,
  // straight lines are the simplest. The API to create straight line segments
  // with the built-in kernel follows the same conventions: the first 2
  // arguments are point tags (the start and end points of the line), and the
  // next one is the line tag.

  // In the commands below, for example, the line 1 starts at point 1 and ends
  // at point 2.

  // Note that curve tags are separate from point tags - hence we can reuse tag
  // `1' for our first curve. And as a general rule, elementary entity tags in
  // Gmsh have to be unique per geometrical dimension.
  gmshModelGeoAddLine(1, 2, 1, &ierr);
  gmshModelGeoAddLine(3, 2, 2, &ierr);
  gmshModelGeoAddLine(3, p4, 3, &ierr);
  gmshModelGeoAddLine(p4, 1, 4, &ierr);

  // The third elementary entity is the surface. In order to define a simple
  // rectangular surface from the four curves defined above, a curve loop has
  // first to be defined. A curve loop is defined by an ordered list of
  // connected curves, a sign being associated with each curve (depending on the
  // orientation of the curve to form a loop). The API function to create curve
  // loops takes a pointer to an array of integers as first argument, the number
  // of elements in the array as the second argument, and the curve loop tag
  // (which must be unique amongst curve loops) as the third argument:
  const int cl1[] = {4, 1, -2, 3};
  gmshModelGeoAddCurveLoop(cl1, sizeof(cl1)/sizeof(cl1[0]), 1, 0, &ierr);

  // We can then define the surface as a list of curve loops (only one here,
  // representing the external contour, since there are no holes): */
  const int s1[] = {1};
  gmshModelGeoAddPlaneSurface(s1, sizeof(s1)/sizeof(s1[0]), 1, &ierr);

  // Before they can be meshed (and, more generally, before they can be used by
  // API functions outside of the built-in CAD kernel functions), the CAD
  // entities must be synchronized with the Gmsh model, which will create the
  // relevant Gmsh data structures. This is achieved by the
  // gmsh.model.geo.synchronize() API call for the built-in CAD
  // kernel. Synchronizations can be called at any time, but they involve a non
  // trivial amount of processing; so while you could synchronize the internal
  // CAD data after every CAD command, it is usually better to minimize the
  // number of synchronization points.
  gmshModelGeoSynchronize(&ierr);

  // At this level, Gmsh knows everything to display the rectangular surface 1
  // and to mesh it. An optional step is needed if we want to group elementary
  // geometrical entities into more meaningful groups, e.g. to define some
  // mathematical ("domain", "boundary"), functional ("left wing", "fuselage")
  // or material ("steel", "carbon") properties.
  //
  // Such groups are called "Physical Groups" in Gmsh. By default, if physical
  // groups are defined, Gmsh will export in output files only mesh elements
  // that belong to at least one physical group. (To force Gmsh to save all
  // elements, whether they belong to physical groups or not, set the
  // `Mesh.SaveAll' option to 1.) Physical groups are also identified by tags,
  // i.e. stricly positive integers, that should be unique per dimension (0D,
  // 1D, 2D or 3D). Physical groups can also be given names.
  //
  // Here we define a physical curve that groups the left, bottom and right
  // curves in a single group (with prescribed tag 5); and a physical surface
  // with name "My surface" (with an automatic tag) containing the geometrical
  // surface 1:
  const int g5[] = {1, 2, 4}, g6[] = {1};
  gmshModelAddPhysicalGroup(1, g5, sizeof(g5)/sizeof(g5[0]), 5, "", &ierr);
  gmshModelAddPhysicalGroup(2, g6, sizeof(g6)/sizeof(g6[0]), -1, "My surface", &ierr);

  // We can then generate a 2D mesh...
  gmshModelMeshGenerate(2, &ierr);

  // ... and save it to disk
  gmshWrite("t1.msh", &ierr);

  // Remember that by default, if physical groups are defined, Gmsh will export
  // in the output mesh file only those elements that belong to at least one
  // physical group. To force Gmsh to save all elements, you can use
  //
  // gmshOptionSetNumber("Mesh.SaveAll", 1, &ierr);

  // By default, Gmsh saves meshes in the latest version of the Gmsh mesh file
  // format (the `MSH' format). You can save meshes in other mesh formats by
  // specifying a filename with a different extension. For example
  //
  // gmshWrite("t1.unv", &ierr);
  //
  // will save the mesh in the UNV format. You can also save the mesh in older
  // versions of the MSH format: simply set
  //
  // gmshOptionSetNumber("Mesh.MshFileVersion", x, &ierr);
  //
  // for any version number `x'. As an alternative, you can also not specify the
  // format explicitly, and just choose a filename with the `.msh2' or `.msh4'
  // extension.

  // To visualize the model we can run the graphical user interface with
  // `gmshFltkRun()'. Here we run it only if "-nopopup" is not provided in the
  // command line arguments:
  int gui = 1;
  for(int i = 0; i < argc; i++) {
    if(!strcmp(argv[i], "-nopopup")) {
      gui = 0;
      break;
    }
  }
  if(gui) gmshFltkRun(&ierr);

  // Note that starting with Gmsh 3.0, models can be built using other geometry
  // kernels than the default "built-in" kernel. To use the OpenCASCADE CAD
  // kernel instead of the built-in kernel, you should use the functions with
  // the "gmshModelOcc" prefix.
  //
  // Different CAD kernels have different features. With OpenCASCADE, instead of
  // defining the surface by successively defining 4 points, 4 curves and 1
  // curve loop, one can define the rectangular surface directly with
  //
  // gmshModelOccAddRectangle(.2, 0, 0, .1, .3, -1, 0, &ierr);
  //
  // After synchronization with the Gmsh model with
  //
  // gmshModelOccSynchronize(&ierr);
  //
  // the underlying curves and points could be accessed with
  // gmshModelGetBoundary(...).

  // This should be called when you are done using the Gmsh C API:
  gmshFinalize(&ierr);
  return 0;
}
