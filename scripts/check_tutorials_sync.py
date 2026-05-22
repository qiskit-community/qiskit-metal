# /// script
# requires-python = ">=3.10"
# ///
"""Check that docs/tut/ and tutorials/ have byte-identical notebook cell content.

The repo carries every numbered notebook twice — once at the canonical
``tutorials/`` location (where users open it in JupyterLab via the file tree)
and once at ``docs/tut/`` with hyphenated filenames (where Sphinx + nbsphinx
build the rendered docs). The two trees MUST stay content-identical or the
docs site silently diverges from what users see when they edit notebooks.

This script compares the ``cells`` array of each pair. It ignores:

- Filename / folder casing (hyphens vs spaces)
- Notebook-level ``metadata`` (kernelspec, language_info — env-dependent)

If you edited only one folder, run::

    python3 _dev/sync_two_folders.py --write

to bring the other into sync (per-notebook canonical choices are baked into
the script). Then re-run this check.

Exits 0 if all 54 pairs are identical, 1 otherwise. Runs in CI on every PR.
"""

import json
import re
import sys
from pathlib import Path


# All numbered + quick-topic pairs. (docs path, tutorials path)
PAIRS = [
    # Section 1
    (
        "docs/tut/1-Overview/1.1-Bird's-eye-view-of-Qiskit-Metal.ipynb",
        "tutorials/1 Overview/1.1 Bird's eye view of Qiskit Metal.ipynb",
    ),
    (
        "docs/tut/1-Overview/1.2-Quick-start.ipynb",
        "tutorials/1 Overview/1.2 Quick start.ipynb",
    ),
    (
        "docs/tut/1-Overview/1.3-Saving-Your-Chip-Design.ipynb",
        "tutorials/1 Overview/1.3 Saving Your Chip Design.ipynb",
    ),
    (
        "docs/tut/1-Overview/1.4-Headless-quick-view-(no-Qt-GUI).ipynb",
        "tutorials/1 Overview/1.4 Headless quick view (no Qt GUI).ipynb",
    ),
    (
        "docs/tut/1-Overview/1.5-Parametric-design---iterate-and-compare.ipynb",
        "tutorials/1 Overview/1.5 Parametric design - iterate and compare.ipynb",
    ),
    (
        "docs/tut/1-Overview/1.6-QComponent-shape-library.ipynb",
        "tutorials/1 Overview/1.6 QComponent shape library.ipynb",
    ),
    # Section 2
    (
        "docs/tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent.ipynb",
        "tutorials/2 From components to chip/A. Using QComponents/2.01 How to use a QComponent.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.02-How-to-copy-a-QComponent.ipynb",
        "tutorials/2 From components to chip/A. Using QComponents/2.02 How to copy a QComponent.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.11-Routing-101.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.11 Routing 101.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.12-Simple-Meander.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.12 Simple Meander.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.13-Hybrid-Auto-and-AStar.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.13 Hybrid Auto and AStar.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.14-Get-them-all-with-MixedRoute.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.14 Get them all with MixedRoute.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip.ipynb",
        "tutorials/2 From components to chip/C. My first full quantum chip design/2.21 Design a 4 qubit full chip.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically.ipynb",
        "tutorials/2 From components to chip/C. My first full quantum chip design/2.22 Design 100 qubits programmatically.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.23-Modify-chip-options.ipynb",
        "tutorials/2 From components to chip/C. My first full quantum chip design/2.23 Modify chip options.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.31-Create-a-QComponent-Basic.ipynb",
        "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.31 Create a QComponent - Basic.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.32-Create-a-QComponent-Advanced.ipynb",
        "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.32 Create a QComponent - Advanced.ipynb",
    ),
    (
        "docs/tut/2-From-components-to-chip/2.33-Add-my-QComponent-to-a-reusable-python-file.ipynb",
        "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.33 Add my QComponent to a reusable python file.ipynb",
    ),
    # Section 3
    (
        "docs/tut/3-Renderers/3.1-Introduction-to-QRenderers.ipynb",
        "tutorials/3 Renderers/3.1 Introduction to QRenderers.ipynb",
    ),
    (
        "docs/tut/3-Renderers/3.2-Export-your-design-to-GDS.ipynb",
        "tutorials/3 Renderers/3.2 Export your design to GDS.ipynb",
    ),
    (
        "docs/tut/3-Renderers/3.3-Render-your-design-to-Ansys.ipynb",
        "tutorials/3 Renderers/3.3 Render your design to Ansys.ipynb",
    ),
    (
        "docs/tut/3-Renderers/3.4-How-do-I-make-my-custom-QRenderer.ipynb",
        "tutorials/3 Renderers/3.4 How do I make my custom QRenderer.ipynb",
    ),
    (
        "docs/tut/3-Renderers/3.5-Render-your-design-to-Gmsh.ipynb",
        "tutorials/3 Renderers/3.5 Render your design to Gmsh.ipynb",
    ),
    # Section 4
    (
        "docs/tut/4-Analysis/4.01-Capacitance-and-LOM.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.01 Capacitance and LOM.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.02-Eigenmode-and-EPR.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.02 Eigenmode and EPR.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.03-Impedance.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.03 Impedance.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.04-New-LOM-and-Fluxonium-Example.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.04 New LOM and Fluxonium Example.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.05 New LOM and Two Coupled Transmon Example.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example-with-sequence.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.05 New LOM and Two Coupled Transmon Example with sequence.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.11-Analyze-and-tune-a-transmon.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.11 Analyze and tune a transmon.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.12-Analyze-a-resonator.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.12 Analyze a resonator.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.13-Analyze-transmon-and-resonator.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.13 Analyze transmon and resonator.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.14-Analyze-a-double-hanger-resonator.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.14 Analyze a double hanger resonator (S Param).ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.15-CPW-kappa-calculation.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.15 CPW kappa calculation.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.16-Analyze-S21-of-Hange-Geometry-with-WirebondLunchpadDriven.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.16 Analyze S21 of Hange Geometry with WirebondLunchpadDriven.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.17-Fit-S21-of-Hanger-Resonator-Geometry.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.17 Fit S21 of Hanger Resonator Geometry.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.18-Analyse-a-Resonator-with-Ports.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.18 Analyse a Resonator with Ports.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.19 Analyze a transmon using ElmerFEM.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.21-Capacitance-matrix.ipynb",
        "tutorials/4 Analysis/C. Parametric sweeps/4.21 Capacitance matrix.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.22-Eigenmode-matrix.ipynb",
        "tutorials/4 Analysis/C. Parametric sweeps/4.22 Eigenmode matrix.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.23-Impedance-and-scattering-Z-S-Y-matrices.ipynb",
        "tutorials/4 Analysis/C. Parametric sweeps/4.23 Impedance and scattering Z S Y matrices.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.31-Plot-quantum-oscillator-wavefunction.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.31 Plot quantum oscillator wavefunction.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.32-Transmon-analytics-HCPB.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.32 Transmon analytics HCPB.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.33-Transmon-analytics.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.33 Transmon analytics.ipynb",
    ),
    (
        "docs/tut/4-Analysis/4.34-Transmon-qubit-CPB-hamiltonian-charge-basis.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.34 Transmon qubit CPB hamiltonian charge basis.ipynb",
    ),
    (
        "docs/tut/4-Analysis/cQED-with-the-Jaynes-Cummings-Interaction-Model.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/cQED with the Jaynes-Cummings Interaction Model.ipynb",
    ),
    (
        "docs/tut/4-Analysis/Design-and-Simulation-of-a-Cross-Resonance-Gate.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/Design and Simulation of a Cross-Resonance Gate.ipynb",
    ),
    # quick-topics / Appendix B
    (
        "docs/tut/quick-topics/JJ-Demo-Notebook.ipynb",
        "tutorials/Appendix B Quick topics/JJ Demo Notebook.ipynb",
    ),
    (
        "docs/tut/quick-topics/Managing-pins.ipynb",
        "tutorials/Appendix B Quick topics/Managing pins.ipynb",
    ),
    (
        "docs/tut/quick-topics/Managing-variables.ipynb",
        "tutorials/Appendix B Quick topics/Managing variables.ipynb",
    ),
    (
        "docs/tut/quick-topics/Opening-documentation.ipynb",
        "tutorials/Appendix B Quick topics/Opening documentation.ipynb",
    ),
    (
        "docs/tut/quick-topics/QComponent-3-fingers-capacitor.ipynb",
        "tutorials/Appendix B Quick topics/QComponent - 3-fingers capacitor.ipynb",
    ),
    (
        "docs/tut/quick-topics/QComponent-Interdigitated-transmon.ipynb",
        "tutorials/Appendix B Quick topics/QComponent - Interdigitated transmon.ipynb",
    ),
    (
        "docs/tut/quick-topics/Testing-QComponents-for-overlap-and-collisions.ipynb",
        "tutorials/Appendix B Quick topics/Testing QComponents for overlap and collisions.ipynb",
    ),
]


def cells_of(path):
    return json.load(open(path))["cells"]


def main():
    drift = []
    missing = []
    for docs_p, tut_p in PAIRS:
        if not Path(docs_p).exists():
            missing.append(f"docs/tut: {docs_p}")
            continue
        if not Path(tut_p).exists():
            missing.append(f"tutorials: {tut_p}")
            continue
        d = cells_of(docs_p)
        t = cells_of(tut_p)
        if json.dumps(d, sort_keys=True) != json.dumps(t, sort_keys=True):
            drift.append((docs_p, tut_p))

    if missing:
        print("ERROR: missing notebook files", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        return 1

    if drift:
        print(
            f"ERROR: {len(drift)} notebook pair(s) drifted between "
            f"docs/tut/ and tutorials/.",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        for docs_p, tut_p in drift:
            print(f"  docs/tut: {docs_p}", file=sys.stderr)
            print(f"  tutorial: {tut_p}", file=sys.stderr)
            print("", file=sys.stderr)
        print(
            "Both folders must contain byte-identical notebook cell content.\n"
            "Re-sync by running:\n\n"
            "    python3 _dev/sync_two_folders.py --write\n\n"
            "Per-notebook canonical choices (which folder wins) are baked\n"
            "into that script's CANONICAL dict. Update them there if you\n"
            "intentionally want a different canonical for a notebook.",
            file=sys.stderr,
        )
        return 1

    print(f"✓ All {len(PAIRS)} notebook pairs in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
