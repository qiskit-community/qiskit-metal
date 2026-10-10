from typing import Dict, Any

try:
    import sequencing as seq
except ImportError as exc:
    # ``sequencing`` is not a dependency of Quantum Metal or of any of its
    # extras (#1231): its last release (1.2.0) calls ``qutip.Options``, which
    # qutip 5 removed, so its simulations cannot run next to qutip >= 5.1.
    raise ImportError(
        "The LOM-to-Sequencing bridge (lom_extensions, lom_time_evolution_sim) "
        "needs the third-party `sequencing` package, which Quantum Metal does "
        "not install: `pip install sequencing`. Note that sequencing 1.2.0 "
        "uses the qutip 4 API, so converting a LOM system works but running "
        "a sequence fails with the qutip >= 5.1 that Quantum Metal requires."
    ) from exc

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
