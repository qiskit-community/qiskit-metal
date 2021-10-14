import sequencing as seq
import numpy as np


class LOMtoSeqMapper:

    @staticmethod
    def mapper(metal_system):
        if metal_system.sys_type == 'TRANSMON':
            return seq.Transmon
        elif metal_system.sys_type in ['FLUXONIUM']:
            return seq.Qubit
        elif metal_system.sys_type in ['TL_RESONATOR', 'LUMPED_RESONATOR']:
            return seq.Cavity


def lom_composite_sys_to_seq_sys(lom_composite,
                                 hilbertspace,
                                 levels=None,
                                 system_name='system'):
    ## FIXME: params for setting detuning and levels
    modes = []

    if levels is None:
        levels = hilbertspace.subsystem_dims

    h_results = lom_composite.hamiltonian_results(hilbertspace,
                                                  print_info=False)
    chi_mat = h_results['chi_in_MHz']
    chi_mat_ghz = chi_mat * 1e-3
    for ii, sub1 in enumerate(lom_composite.subsystems):
        seq_cls = sub1.map_to_custom_system(LOMtoSeqMapper.mapper)
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
