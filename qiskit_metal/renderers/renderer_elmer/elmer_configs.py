"""Configuration settings used by ElemerFEM. For details, please refer
to the ElmerFEM documentation http://www.elmerfem.org/blog/documentation/
"""

# Dictionary containing a database of materials and their properties to be
# assigned to an ElmerFEM model.
materials = dict(
    vacuum={
        "Electric Conductivity": 0.0,
        "Relative Permittivity": 1,
    },
    silicon={
        "Relative Permittivity": 11.45,
    },
)

# Dictionary containing valid ElmerFEM simulation types and dimensions with
# their correspoding settings (e.g. steady state 3D, transient 2D, etc.).
simulations = dict(
    steady_3D={
        "Max Output Level": 5,
        "Coordinate System": "Cartesian",
        "Coordinate Mapping(3)": "1 2 3",
        "Simulation Type": "Steady state",
        "Steady State Max Iterations": 1,
        "Output Intervals": 1,
        "Timestepping Method": "BDF",
        "BDF Order": 1,
        "Solver Input File": "case.sif",
        "Post File": "case.ep",
        "Output File": "case.result",
    })

# Dictionary containing valid ElmerFEM solvers and their correspoding
# settings (e.g. StatElecSolver, ResultOutputSolve, etc.).
solvers = dict(
    capacitance={
        "Equation": "Electrostatics",
        "Calculate Electric Field": True,
        "Calculate Capacitance Matrix": True,
        "Capacitance Matrix Filename": "capacitance.txt",
        "Procedure": '"StatElecSolve" "StatElecSolver"',
        "Variable": "Potential",
        "Calculate Electric Energy": True,
        "Exec Solver": "Always",
        "Stabilize": True,
        "Bubbles": False,
        "Lumped Mass Matrix": False,
        "Optimize Bandwidth": True,
        "Steady State Convergence Tolerance": 1.0e-5,
        "Nonlinear System Convergence Tolerance": 1.0e-7,
        "Nonlinear System Max Iterations": 20,
        "Nonlinear System Newton After Iterations": 3,
        "Nonlinear System Newton After Tolerance": 1.0e-3,
        "Nonlinear System Relaxation Factor": 1,
        "Linear System Solver": "Iterative",
        "Linear System Iterative Method": "BiCGStab",
        "Linear System Max Iterations": 500,
        "Linear System Convergence Tolerance": 1.0e-10,
        "BiCGstabl polynomial degree": 2,
        "Linear System Preconditioning": "ILU0",
        "Linear System ILUT Tolerance": 1.0e-3,
        "Linear System Abort Not Converged": False,
        "Linear System Residual Output": 10,
        "Linear System Precondition Recompute": 1,
    },
    postprocessing_gmsh={
        "Exec Solver": "Always",
        "Equation": "Result Output",
        "Procedure": '"ResultOutputSolve" "ResultOutputSolver"',
        "Output File Name": '"case"',
        "Output Format": "gmsh",
    },
)
