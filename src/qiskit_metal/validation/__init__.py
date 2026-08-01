# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Design-rule checking (DRC) for Quantum Metal designs.

Checks a built design for layout defects that render without complaint but
are wrong: shorted nets, features off the chip, routes too close to a qubit,
corners too tight to fillet.

    >>> from qiskit_metal.validation import validate
    >>> result = validate(design)
    >>> print(result)
    >>> result.raise_if_errors()          # for a build script or CI gate

Rules carry thresholds, so a process design kit that differs from the
defaults is a constructor argument rather than a fork::

    from qiskit_metal.validation import validate, MetalSpacingRule, DEFAULT_RULES
    validate(design, rules=[*DEFAULT_RULES, MetalSpacingRule(min_spacing="4um")])

Defaults follow published superconducting-chip design-rule sets where one
exists -- see :mod:`qiskit_metal.validation.rules` for the per-rule
provenance. They are a starting point, not a guarantee for any particular
foundry.

Severity: ERROR is geometry that is wrong regardless of intent; WARNING is
legal geometry that is probably unintended or spends a physical budget
(loss, stray coupling). Only ERRORs make a result falsy or raise.
"""

from .core import (
    DesignRule,
    DesignRuleViolation,
    Finding,
    Severity,
    ValidationResult,
)
from .rules import (
    DEFAULT_RULES,
    ChipBoundsRule,
    CPWGapRule,
    MetalOverlapRule,
    MetalSpacingRule,
    QubitClearanceRule,
    ShortSegmentRule,
)

__all__ = [
    "DEFAULT_RULES",
    "CPWGapRule",
    "ChipBoundsRule",
    "DesignRule",
    "DesignRuleViolation",
    "Finding",
    "MetalOverlapRule",
    "MetalSpacingRule",
    "QubitClearanceRule",
    "Severity",
    "ShortSegmentRule",
    "ValidationResult",
    "validate",
]


def validate(design, rules=None, strict=False) -> ValidationResult:
    """Run design rules over ``design``.

    Args:
        design (QDesign): a built design. Call ``design.rebuild()`` first if
            components changed -- rules read the qgeometry tables, not the
            component options.
        rules (Iterable[DesignRule]): rules to run. Defaults to
            :data:`~qiskit_metal.validation.rules.DEFAULT_RULES`.
        strict (bool): raise :class:`DesignRuleViolation` if any
            ERROR-severity finding is produced. Equivalent to calling
            :meth:`ValidationResult.raise_if_errors` on the result.

    Returns:
        ValidationResult: findings, in the order the rules ran.

    Raises:
        DesignRuleViolation: if ``strict`` and any ERROR was found.
    """
    chosen = tuple(DEFAULT_RULES if rules is None else rules)
    findings = []
    for rule in chosen:
        findings.extend(rule.check(design))
    result = ValidationResult(
        findings=findings, rules_run=tuple(r.name for r in chosen)
    )
    if strict:
        result.raise_if_errors()
    return result
