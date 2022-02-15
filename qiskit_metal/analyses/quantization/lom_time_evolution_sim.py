import sequencing as seq
import numpy as np
import scqubits as scq
from typing import List

from qiskit_metal.analyses.quantization.lom_core_analysis import CompositeSystem, Subsystem
from qiskit_metal.analyses.quantization.lom_extensions import LOM_SUBSYSTEM_TO_SEQ_MODE, to_external_system


def lom_composite_sys_to_seq_sys(lom_composite: CompositeSystem,
                                 hilbertspace: scq.HilbertSpace,
                                 levels: List[int] = None,
                                 system_name='system') -> seq.System:
    ## TODO: params for setting detuning and levels
    """Convert LOM composite system to Sequencing system. A 'subsystem' in
    LOM composite system corresponds to a 'mode' in Sequencing system

    Args:
        lom_composite (CompositeSystem): Metal LOM composite system
        hilbertspace (scq.HilbertSpace): The hilbertspace of the passed LOM composite system
        levels (List[int], optional): Number of energy levels to keep for each mode in
            Sequencing system. If None, use the LOM subsystems' respective dimensions.
            Defaults to None.
        system_name (str, optional): [description]. Defaults to 'system'.

    Returns:
        seq.System: the converted Sequencing system
    """

    modes = []

    if levels is None:
        levels = hilbertspace.subsystem_dims

    h_results = lom_composite.hamiltonian_results(hilbertspace,
                                                  print_info=False)
    chi_mat = h_results['chi_in_MHz']
    chi_mat_ghz = chi_mat * 1e-3
    for ii, sub1 in enumerate(lom_composite.subsystems):
        seq_cls = to_external_system(sub1, LOM_SUBSYSTEM_TO_SEQ_MODE)
        sub_name = sub1.name
        self_kerr = chi_mat_ghz[ii, ii]
        mode = seq_cls(sub_name, levels=levels[ii], kerr=self_kerr)
        modes.append(mode)

    system = seq.System(system_name, modes=modes)
    for ii in range(len(modes)):
        mode1 = modes[ii]
        for jj in range(ii + 1, len(modes)):
            mode2 = modes[jj]
            cross_kerr = chi_mat_ghz[ii, jj]
            system.set_cross_kerr(mode1, mode2, chi=cross_kerr)

    return system
