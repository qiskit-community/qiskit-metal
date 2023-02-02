// -----------------------------------------------------------------------------
//
//  Gmsh C++ extended tutorial 4
//
//  Post-processing data import: model-based
//
// -----------------------------------------------------------------------------

#include <set>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);

  // Contrary to list-based view (see `x3.cpp'), model-based views are based on
  // one or more meshes. Compared to list-based views, they are thus linked to
  // one model (per step). Post-processing data stored in MSH files create such
  // model-based views.

  // Let's create a first model-based view using a simple mesh constructed by
  // hand. We create a model with a discrete surface
  gmsh::model::add("simple model");
  int surf = gmsh::model::addDiscreteEntity(2);

  // We add 4 nodes and 2 3-node triangles (element type "2")
  gmsh::model::mesh::addNodes(2, surf, {1, 2, 3, 4},
                              {0., 0., 0., 1., 0., 0., 1., 1., 0., 0., 1., 0.});
  gmsh::model::mesh::addElementsByType(surf, 2, {1, 2}, {1, 2, 3, 1, 3, 4});

  // We can now create a new model-based view, to which we add 10 steps of
  // node-based data:
  int t1 = gmsh::view::add("A model-based view");
  for(int step = 0; step < 10; step++) {
    gmsh::view::addHomogeneousModelData(
      t1, step, "simple model", "NodeData", {1, 2, 3, 4}, // tags of nodes
      {10., 10., 12. + step, 13. + step}); // data, per node
  }

  // Besided node-based data, which result in continuous fields, one can also
  // add general discontinous fields defined at the nodes of each element, using
  // "ElementNodeData":
  int t2 = gmsh::view::add("A discontinuous model-based view");
  for(int step = 0; step < 10; step++) {
    gmsh::view::addHomogeneousModelData(
      t2, step, "simple model", "ElementNodeData", {1, 2}, // tags of elements
      {10., 10., 12. + step, 14., 15., 13. + step}); // data per element nodes
  }

  // Constant per element datasets can also be created using "ElementData". Note
  // that a more general function `addModelData' to add data for hybrid meshes
  // (when data is not homogeneous, i.e. when the number of nodes changes
  // between elements) is also available.

  // Each step of a model-based view can be defined on a different model,
  // i.e. on a different mesh. Let's define a second model and mesh it
  gmsh::model::add("another model");
  gmsh::model::occ::addBox(0, 0, 0, 1, 1, 1);
  gmsh::model::occ::synchronize();
  gmsh::model::mesh::generate(3);

  // We can add other steps to view "t" based on this new mesh:
  std::vector<std::size_t> nodes;
  std::vector<double> coord, coordParam;
  gmsh::model::mesh::getNodes(nodes, coord, coordParam);
  for(int step = 11; step < 20; step++) {
    std::vector<double> val;
    for(std::size_t i = 0; i < coord.size(); i += 3)
      val.push_back(step * coord[i]);
    gmsh::view::addHomogeneousModelData(t1, step, "another model", "NodeData",
                                        nodes, val);
  }

  // This feature allows to create seamless animations for time-dependent
  // datasets on deforming or remeshed models.

  // High-order node-based datasets are supported without needing to supply the
  // interpolation matrices (iso-parametric Lagrange elements). Arbitrary
  // high-order datasets can be specified as "ElementNodeData", with the
  // interpolation matrices specified in the same as as for list-based views
  // (see `x3.cpp').

  // Model-based views can be saved to disk using `gmsh::view::write()'; note
  // that saving a view based on multiple meshes (like the view `t1') will
  // automatically create several files. If the `PostProcessing.SaveMesh' option
  // is not set, `gmsh::view::write()' will only save the view data, without the
  // mesh (which could be saved independently with `gmsh::write()').
  gmsh::view::write(t1, "x4_t1.msh");
  gmsh::view::write(t2, "x4_t2.msh");

  // Launch the GUI to see the results:
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
