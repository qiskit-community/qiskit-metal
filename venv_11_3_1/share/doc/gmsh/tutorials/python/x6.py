# -----------------------------------------------------------------------------
#
#  Gmsh Python extended tutorial 6
#
#  Additional mesh data: integration points, Jacobians and basis functions
#
# -----------------------------------------------------------------------------

import gmsh
import sys

gmsh.initialize(sys.argv)

gmsh.model.add("x6")

# The API provides access to all the elementary building blocks required to
# implement finite-element-type numerical methods. Let's create a simple 2D
# model and mesh it:
gmsh.model.occ.addRectangle(0, 0, 0, 1, 0.1)
gmsh.model.occ.synchronize()
gmsh.model.mesh.setTransfiniteAutomatic()
gmsh.model.mesh.generate(2)

# Set the element order and the desired interpolation order:
elementOrder = 1
interpolationOrder = 2
gmsh.model.mesh.setOrder(elementOrder)

def pp(label, v, mult):
    print(" * " + str(len(v) / mult) + " " + label + ": " + str(v))

# Iterate over all the element types present in the mesh:
elementTypes = gmsh.model.mesh.getElementTypes()

for t in elementTypes:
    # Retrieve properties for the given element type
    elementName, dim, order, numNodes, numPrimNodes, localNodeCoord =\
    gmsh.model.mesh.getElementProperties(t)
    print("\n** " + elementName + " **\n")

    # Retrieve integration points for that element type, enabling exact
    # integration of polynomials of order "interpolationOrder". The "Gauss"
    # integration family returns the "economical" Gauss points if available, and
    # defaults to the "CompositeGauss" (tensor product) rule if not.
    localCoords, weights =\
    gmsh.model.mesh.getIntegrationPoints(t, "Gauss" + str(interpolationOrder))
    pp("integration points to integrate order " +
       str(interpolationOrder) + " polynomials", localCoords, 3)

    # Return the basis functions evaluated at the integration points. Selecting
    # "Lagrange" and "GradLagrange" returns the isoparamtric basis functions and
    # their gradient (in the reference space of the given element type). A
    # specific interpolation order can be requested using "LagrangeN" and
    # "GradLagrangeN" with N = 1, 2, ... Other supported function spaces include
    # "H1LegendreN", "GradH1LegendreN", "HcurlLegendreN", "CurlHcurlLegendreN".
    numComponents, basisFunctions, numOrientations =\
    gmsh.model.mesh.getBasisFunctions(t, localCoords, "Lagrange")
    pp("basis functions at integration points", basisFunctions, 1)
    numComponents, basisFunctions, numOrientations =\
    gmsh.model.mesh.getBasisFunctions(t, localCoords, "GradLagrange")
    pp("basis function gradients at integration points", basisFunctions, 3)

    # Compute the Jacobians (and their determinants) at the integration points
    # for all the elements of the given type in the mesh. Beware that the
    # Jacobians are returned "by column": see the API documentation for details.
    jacobians, determinants, coords =\
    gmsh.model.mesh.getJacobians(t, localCoords)
    pp("Jacobian determinants at integration points", determinants, 1)

gmsh.finalize()
