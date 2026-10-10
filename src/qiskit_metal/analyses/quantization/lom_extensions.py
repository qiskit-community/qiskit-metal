from typing import Dict, Any

try:
    import sequencing as seq
except ImportError as exc:
    # ``sequencing`` is not a dependency of Quantum Metal or of any of its
    # extras (#1231). Its last release (1.2.0) is written for qutip 4;
    # ``_sequencing_compat`` adapts it to qutip 5 below.
    raise ImportError(
        "The LOM-to-Sequencing bridge (lom_extensions, lom_time_evolution_sim) "
        "needs the third-party `sequencing` package, which Quantum Metal does "
        "not install: `pip install sequencing`. sequencing 1.2.0 is written "
        "for qutip 4; Quantum Metal adapts its solver calls to qutip 5 when "
        "this module is imported."
    ) from exc

from qiskit_metal.analyses.quantization import _sequencing_compat

_sequencing_compat.apply()

from qiskit_metal.analyses.quantization.lom_core_analysis import Subsystem


def to_external_system(lom_subsystem: Subsystem, mapping: dict[str, Any]):
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
            f"LOM subsystem of type {lom_subsystem.sys_type} cannot be converted to an extern system."
        )

    return mapping[lom_subsystem.sys_type]


##-----------------------------------------------------------------------------------
## Add new custom external system mapping or modify or extend existing mappings here
##-----------------------------------------------------------------------------------

LOM_SUBSYSTEM_TO_SEQ_MODE = {
    "TRANSMON": seq.Transmon,
    "FLUXONIUM": seq.Qubit,
    "TL_RESONATOR": seq.Cavity,
    "LUMPED_RESONATOR": seq.Cavity,
}
