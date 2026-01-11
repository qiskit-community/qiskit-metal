from typing import Dict, Any
import sequencing as seq

from qiskit_metal.analyses.quantization.lom_core_analysis import Subsystem


def to_external_system(lom_subsystem: Subsystem, mapping: Dict[str, Any]):
    """Convert a Metal LOM subsystem to an external system based on a custom mapping

    Args:
        lom_subsystem (Subsystem): the LOM subsystem
        mapping (Dict[str, Any]): custom mapping for the conversion,
            where the keys are LOM subsystem types and values are
            the custom external systems (which can be arbitrary types)

    Raises:
        ValueError: throws when the provided LOM subsystem type
            doesn't exist in the custom mapping

    Returns:
        [type]: external system
    """
    if lom_subsystem.sys_type not in mapping:
        raise ValueError(
            f'LOM subsystem of type {lom_subsystem.sys_type} cannot be converted to an extern system.'
        )

    return mapping[lom_subsystem.sys_type]


##-----------------------------------------------------------------------------------
## Add new custom external system mapping or modify or extend existing mappings here
##-----------------------------------------------------------------------------------

LOM_SUBSYSTEM_TO_SEQ_MODE = {
    'TRANSMON': seq.Transmon,
    'FLUXONIUM': seq.Qubit,
    'TL_RESONATOR': seq.Cavity,
    'LUMPED_RESONATOR': seq.Cavity
}
