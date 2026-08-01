# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Design-rule gate on the Appendix A reference designs.

The reference notebooks are what a new user copies, so a defect in one
propagates. This runs each of them through
:func:`qiskit_metal.validation.validate` and fails on any error, plus on
any warning not already recorded in ``KNOWN_WARNINGS``.

The allowlist follows the ``KNOWN_INWARD_PINS`` precedent in
``test_qlibrary_pin_sanity.py``: existing defects are written down so they
stay visible, while anything new fails the build. Shrinking an entry is
always allowed; growing one needs a reason.
"""

import json
import re
import unittest
from pathlib import Path

from qiskit_metal.validation import Severity, validate

REFERENCE_DIR = (
    Path(__file__).resolve().parents[1]
    / "tutorials"
    / "Appendix A Full design flow examples"
)

NOTEBOOKS = (
    "Reference design 1 - Transmon with readout resonator.ipynb",
    "Reference design 2 - Two coupled transmons.ipynb",
    "Reference design 3 - Four-qubit multiplexed readout.ipynb",
)

#: Lines that draw rather than build, plus comments and magics. Drawing
#: tells us nothing about the geometry and needs a display.
_DRAWING = re.compile(
    r"^\s*(#|%|!|$"
    r"|.*\bqm\.(view|show_inline)\b"
    r"|.*\bMetalGUI\b"
    r"|.*\bplt\."
    r"|.*\.savefig\b)"
)

#: ``{notebook stem: {rule name: warning count}}`` -- known, tolerated.
#:
#: ``short-segment``: both designs route with a 90 um fillet through
#: pathfinder jogs shorter than the 180 um a corner arc needs. Cosmetic in
#: the mpl view, but the GDS and gmsh renderers drop the fillet there.
KNOWN_WARNINGS = {
    "Reference design 2 - Two coupled transmons": {"short-segment": 2},
    "Reference design 3 - Four-qubit multiplexed readout": {"short-segment": 2},
}


def _build(path: Path):
    """Execute a notebook's geometry cells and return its ``design``."""
    notebook = json.loads(path.read_text())
    # Whole cells are skipped, not individual lines: `fig = qm.view(design)`
    # followed by `qm.show_inline(fig)` only makes sense together. A cell
    # that mixes drawing with geometry is therefore kept and executed --
    # matplotlib's Agg backend handles that headlessly.
    source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and not all(_DRAWING.match(line) for line in cell["source"])
    )
    namespace: dict = {}
    exec(compile(source, str(path), "exec"), namespace)  # noqa: S102
    design = namespace["design"]
    design.rebuild()
    return design


class TestReferenceDesigns(unittest.TestCase):
    """Every shipped reference design must pass its own design rules."""

    def test_notebooks_are_present(self):
        missing = [n for n in NOTEBOOKS if not (REFERENCE_DIR / n).is_file()]
        self.assertEqual(missing, [], msg=f"reference notebooks moved: {missing}")

    def test_no_errors_and_no_new_warnings(self):
        for name in NOTEBOOKS:
            with self.subTest(notebook=name):
                result = validate(_build(REFERENCE_DIR / name))

                self.assertEqual(
                    [f.message for f in result.errors],
                    [],
                    msg=f"{name} has design-rule errors",
                )

                counts: dict[str, int] = {}
                for finding in result.findings:
                    if finding.severity is Severity.WARNING:
                        counts[finding.rule] = counts.get(finding.rule, 0) + 1

                known = KNOWN_WARNINGS.get(Path(name).stem, {})
                new = {rule: n for rule, n in counts.items() if n > known.get(rule, 0)}
                self.assertEqual(
                    new,
                    {},
                    msg=(
                        f"{name} gained design-rule warnings beyond the "
                        f"recorded baseline {known}: {new}. Fix the design, "
                        "or update KNOWN_WARNINGS with the reason."
                    ),
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
