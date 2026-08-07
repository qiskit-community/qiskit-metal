# /// script
# requires-python = ">=3.10"
# ///
"""Check that the docs/ and tutorials/ notebook copies have byte-identical cells.

The repo carries every published notebook twice — once at the canonical
``tutorials/`` location (where users open it in JupyterLab via the file tree)
and once under ``docs/`` with hyphenated filenames (where Sphinx + nbsphinx
build the rendered docs). Two docs trees mirror ``tutorials/``:

- ``docs/tut/`` — the numbered notebooks plus Appendix B, and the three
  Appendix A reference designs
- ``docs/circuit-examples/`` — Appendix C, plus the remaining Appendix A
  full-design-flow examples

The trees MUST stay content-identical or the docs site silently diverges from
what users see when they edit notebooks. ``docs/circuit-examples/`` was
unpaired until v0.8.x and had drifted across all 23 of its notebooks.

This script compares the ``cells`` array of each pair. It ignores:

- Filename / folder casing (hyphens vs spaces)
- Notebook-level ``metadata`` (kernelspec, language_info — env-dependent)

Cell ``outputs`` are compared, not ignored: both sides must carry the same
stored outputs, since nbsphinx renders them as-is (``nbsphinx_execute`` is
"never" unless QISKIT_DOCS_BUILD_TUTORIALS says otherwise).

If you edited only one folder, run::

    python3 _dev/sync_two_folders.py --write

to bring the other into sync (per-notebook canonical choices are baked into
the script). Then re-run this check.

Exits 0 if all pairs are identical, 1 otherwise. Runs in CI on every PR.
"""

import json
import re
import sys
from pathlib import Path


# Every published pair. (docs path, tutorials path)
PAIRS = [
    # Section 1
    (
        "docs/tut/1-Overview/1.2-Bird's-eye-view-of-Quantum-Metal.ipynb",
        "tutorials/1 Overview/1.2 Bird's eye view of Quantum Metal.ipynb",
    ),
    (
        "docs/tut/1-Overview/1.1-Quick-start.ipynb",
        "tutorials/1 Overview/1.1 Quick start.ipynb",
    ),
    (
        "docs/tut/1-Overview/1.3-Build-a-4-qubit-chip.ipynb",
        "tutorials/1 Overview/1.3 Build a 4-qubit chip.ipynb",
    ),
    (
        "docs/tut/1-Overview/1.4-Saving-Your-Chip-Design.ipynb",
        "tutorials/1 Overview/1.4 Saving Your Chip Design.ipynb",
    ),
    (
        "docs/tut/1-Overview/1.5-Parametric-design---iterate-and-compare.ipynb",
        "tutorials/1 Overview/1.5 Parametric design - iterate and compare.ipynb",
    ),
    # Section 2
    (
        "docs/tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent.ipynb",
        "tutorials/2 From components to chip/A. Using QComponents/2.01 How to use a QComponent.ipynb",
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
        "docs/tut/2-From-components-to-chip/2.15-Airbridges.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.15 Airbridges.ipynb",
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
        "docs/tut/2-From-components-to-chip/2.24-Design-rule-checking.ipynb",
        "tutorials/2 From components to chip/C. My first full quantum chip design/2.24 Design rule checking.ipynb",
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
    # full-design-examples / Appendix A
    (
        "docs/tut/full-design-examples/Reference-design-1-Transmon-with-readout-resonator.ipynb",
        "tutorials/Appendix A Full design flow examples/Reference design 1 - Transmon with readout resonator.ipynb",
    ),
    (
        "docs/tut/full-design-examples/Reference-design-2-Two-coupled-transmons.ipynb",
        "tutorials/Appendix A Full design flow examples/Reference design 2 - Two coupled transmons.ipynb",
    ),
    (
        "docs/tut/full-design-examples/Reference-design-3-Four-qubit-multiplexed-readout.ipynb",
        "tutorials/Appendix A Full design flow examples/Reference design 3 - Four-qubit multiplexed readout.ipynb",
    ),
    # circuit-examples / Appendix C + Appendix A
    (
        "docs/circuit-examples/A.Qubits/01-Transmon_cross.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/01-Transmon_cross.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/02-Transmon_floating.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/02-Transmon_floating.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/03-concentric_transmon.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/03-concentric_transmon.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/04-Interdigitated_Transmon.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/04-Interdigitated_Transmon.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/05-Transmon_cross_fl.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/05-Transmon_cross_fl.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/06-Transmon_floating_6.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/06-Transmon_floating_6.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/07-Transmon_floating_cl.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/07-Transmon_floating_cl.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/08-JJ-Dolan.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/08-JJ-Dolan.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/09-JJ-Manhattan.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/09-JJ-Manhattan.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/10-Transmon_floating_teeth.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/10-Transmon_floating_teeth.ipynb",
    ),
    (
        "docs/circuit-examples/A.Qubits/11-Star_shaped_qubit.ipynb",
        "tutorials/Appendix C Circuit examples/A. Qubits/11-Star_shaped_qubit.ipynb",
    ),
    (
        "docs/circuit-examples/B.Resonators/11-Resonator_Meander.ipynb",
        "tutorials/Appendix C Circuit examples/B. Resonators/11-Resonator_Meander.ipynb",
    ),
    (
        "docs/circuit-examples/C.Composite-bi-partite/21-OneTransmonsWithMeanderAndOTG.ipynb",
        "tutorials/Appendix C Circuit examples/C. Composite-bi-partite/21-OneTransmonsWithMeanderAndOTG.ipynb",
    ),
    (
        "docs/circuit-examples/D.Qubit-couplers/31-TwoCrossmonsTunableCoupler.ipynb",
        "tutorials/Appendix C Circuit examples/D. Qubit-couplers/31-TwoCrossmonsTunableCoupler.ipynb",
    ),
    (
        "docs/circuit-examples/D.Qubit-couplers/32-TwoTransmonsDirectCoupling.ipynb",
        "tutorials/Appendix C Circuit examples/D. Qubit-couplers/32-TwoTransmonsDirectCoupling.ipynb",
    ),
    (
        "docs/circuit-examples/D.Qubit-couplers/33-TwoTransmonsWithMeander.ipynb",
        "tutorials/Appendix C Circuit examples/D. Qubit-couplers/33-TwoTransmonsWithMeander.ipynb",
    ),
    (
        "docs/circuit-examples/E.Input-output-coupling/41-LaunchPad.ipynb",
        "tutorials/Appendix C Circuit examples/E. Input-output-coupling/41-LaunchPad.ipynb",
    ),
    (
        "docs/circuit-examples/E.Input-output-coupling/42-ResonatorAndLaunchPad.ipynb",
        "tutorials/Appendix C Circuit examples/E. Input-output-coupling/42-ResonatorAndLaunchPad.ipynb",
    ),
    (
        "docs/circuit-examples/E.Input-output-coupling/43-TransmonPocketCL.ipynb",
        "tutorials/Appendix C Circuit examples/E. Input-output-coupling/43-TransmonPocketCL.ipynb",
    ),
    (
        "docs/circuit-examples/F.Small-quantum-chips/51-Four_qubit_chip.ipynb",
        "tutorials/Appendix C Circuit examples/F. Small-quantum-chips/51-Four_qubit_chip.ipynb",
    ),
    (
        "docs/circuit-examples/full-design-flow-examples/Example-full-chip-design.ipynb",
        "tutorials/Appendix A Full design flow examples/Example full chip design.ipynb",
    ),
    (
        "docs/circuit-examples/full-design-flow-examples/Example-used-in-the-launch-video.ipynb",
        "tutorials/Appendix A Full design flow examples/Example used in the launch video.ipynb",
    ),
    (
        "docs/circuit-examples/full-design-flow-examples/Exercise-for-the-South-Korea-Hackathon'20.ipynb",
        "tutorials/Appendix A Full design flow examples/Exercise for the South Korea Hackathon'20.ipynb",
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
        print(file=sys.stderr)
        for docs_p, tut_p in drift:
            print(f"  docs/tut: {docs_p}", file=sys.stderr)
            print(f"  tutorial: {tut_p}", file=sys.stderr)
            print(file=sys.stderr)
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
