// -----------------------------------------------------------------------------
//
//  Gmsh C++ extended tutorial 6
//
//  Additional mesh data: integration points, Jacobians and basis functions
//
// -----------------------------------------------------------------------------

#include <iostream>
#include <gmsh.h>

int main(int argc, char **argv)
{
  gmsh::initialize(argc, argv);
  gmsh::model::add("x6");

  // The API provides access to all the elementary building blocks required to
  // implement finite-element-type numerical methods. Let's create a simple 2D
  // model and mesh it:
  gmsh::model::occ::addRectangle(0, 0, 0, 1, 0.1);
  gmsh::model::occ::synchronize();
  gmsh::model::mesh::setTransfiniteAutomatic();
  gmsh::model::mesh::generate(2);

  // Set the element order and the desired interpolation order:
  int elementOrder = 1, interpolationOrder = 2;
  gmsh::model::mesh::setOrder(elementOrder);

  auto pp = [](const std::string &label, const std::vector<double> &v, int mult)
  {
    std::cout << " * " << v.size() / mult << " " << label << ": ";
    for(auto c : v) std::cout << c << " ";
    std::cout << "\n";
  };

  // Iterate over all the element types present in the mesh:
  std::vector<int> elementTypes;
  gmsh::model::mesh::getElementTypes(elementTypes);
  for(auto t : elementTypes) {
    // Retrieve properties for the given element type
    std::string elementName;
    int dim, order, numNodes, numPrimNodes;
    std::vector<double> localNodeCoord;
    gmsh::model::mesh::getElementProperties
      (t, elementName, dim, order, numNodes, localNodeCoord, numPrimNodes);
    std::cout << "\n** " << elementName << " **\n\n";

    // Retrieve integration points for that element type, enabling exact
    // integration of polynomials of order "interpolationOrder". The "Gauss"
    // integration family returns the "economical" Gauss points if available,
    // and defaults to the "CompositeGauss" (tensor product) rule if not.
    std::vector<double> localCoords, weights;
    gmsh::model::mesh::getIntegrationPoints
      (t, "Gauss" + std::to_string(interpolationOrder), localCoords, weights);
    pp("integration points to integrate order " +
       std::to_string(interpolationOrder) + " polynomials", localCoords, 3);

    // Return the basis functions evaluated at the integration points. Selecting
    // "Lagrange" and "GradLagrange" returns the isoparamtric basis functions
    // and their gradient (in the reference space of the given element type). A
    // specific interpolation order can be requested using "LagrangeN" and
    // "GradLagrangeN" with N = 1, 2, ... Other supported function spaces
    // include "H1LegendreN", "GradH1LegendreN", "HcurlLegendreN",
    // "CurlHcurlLegendreN".
    int numComponents, numOrientations;
    std::vector<double> basisFunctions;
    gmsh::model::mesh::getBasisFunctions
      (t, localCoords, "Lagrange", numComponents, basisFunctions,
       numOrientations);
    pp("basis functions at integration points", basisFunctions, 1);
    gmsh::model::mesh::getBasisFunctions
      (t, localCoords, "GradLagrange", numComponents, basisFunctions,
       numOrientations);
    pp("basis function gradients at integration points", basisFunctions, 3);

    // Compute the Jacobians (and their determinants) at the integration points
    // for all the elements of the given type in the mesh. Beware that the
    // Jacobians are returned "by column": see the API documentation for
    // details.
    std::vector<double> jacobians, determinants, coords;
    gmsh::model::mesh::getJacobians
      (t, localCoords, jacobians, determinants, coords);
    pp("Jacobian determinants at integration points", determinants, 1);
  }

  gmsh::finalize();
  return 0;
}
