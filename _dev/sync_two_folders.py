"""Sync notebooks between docs/tut/ and tutorials/ based on per-notebook canonical choice.

Usage:
  python3 _dev/sync_two_folders.py                # dry-run
  python3 _dev/sync_two_folders.py --write        # apply

Per-notebook policy (set in CANONICAL dict below):
  'tut'  → tutorials/ is canonical, copy tutorials → docs/tut (overwrite docs/tut)
  'docs' → docs/tut/ is canonical, copy docs/tut → tutorials (overwrite tutorials)

After running, both folders contain identical cell content (just different
filenames/folder names: hyphenated in docs/tut/, spaces in tutorials/).
"""

import json
import shutil
import sys
from pathlib import Path

# (docs/tut path, tutorials path) — every pair in sections 1, 2, 3, 4, quick-topics
PAIRS = {
    # --- Section 1 ---
    '1.1': ("docs/tut/1-Overview/1.1-Bird's-eye-view-of-Qiskit-Metal.ipynb",
            "tutorials/1 Overview/1.1 Bird's eye view of Qiskit Metal.ipynb"),
    '1.2': ("docs/tut/1-Overview/1.2-Quick-start.ipynb",
            "tutorials/1 Overview/1.2 Quick start.ipynb"),
    '1.3': ("docs/tut/1-Overview/1.3-Saving-Your-Chip-Design.ipynb",
            "tutorials/1 Overview/1.3 Saving Your Chip Design.ipynb"),
    '1.4': ("docs/tut/1-Overview/1.4-Headless-quick-view-(no-Qt-GUI).ipynb",
            "tutorials/1 Overview/1.4 Headless quick view (no Qt GUI).ipynb"),
    '1.5': ("docs/tut/1-Overview/1.5-Parametric-design---iterate-and-compare.ipynb",
            "tutorials/1 Overview/1.5 Parametric design - iterate and compare.ipynb"),
    '1.6': ("docs/tut/1-Overview/1.6-QComponent-shape-library.ipynb",
            "tutorials/1 Overview/1.6 QComponent shape library.ipynb"),
    # --- Section 2 ---
    '2.01': ("docs/tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent.ipynb",
             "tutorials/2 From components to chip/A. Using QComponents/2.01 How to use a QComponent.ipynb"),
    '2.02': ("docs/tut/2-From-components-to-chip/2.02-How-to-copy-a-QComponent.ipynb",
             "tutorials/2 From components to chip/A. Using QComponents/2.02 How to copy a QComponent.ipynb"),
    '2.11': ("docs/tut/2-From-components-to-chip/2.11-Routing-101.ipynb",
             "tutorials/2 From components to chip/B. Routing between QComponents/2.11 Routing 101.ipynb"),
    '2.12': ("docs/tut/2-From-components-to-chip/2.12-Simple-Meander.ipynb",
             "tutorials/2 From components to chip/B. Routing between QComponents/2.12 Simple Meander.ipynb"),
    '2.13': ("docs/tut/2-From-components-to-chip/2.13-Hybrid-Auto-and-AStar.ipynb",
             "tutorials/2 From components to chip/B. Routing between QComponents/2.13 Hybrid Auto and AStar.ipynb"),
    '2.14': ("docs/tut/2-From-components-to-chip/2.14-Get-them-all-with-MixedRoute.ipynb",
             "tutorials/2 From components to chip/B. Routing between QComponents/2.14 Get them all with MixedRoute.ipynb"),
    '2.21': ("docs/tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip.ipynb",
             "tutorials/2 From components to chip/C. My first full quantum chip design/2.21 Design a 4 qubit full chip.ipynb"),
    '2.22': ("docs/tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically.ipynb",
             "tutorials/2 From components to chip/C. My first full quantum chip design/2.22 Design 100 qubits programmatically.ipynb"),
    '2.23': ("docs/tut/2-From-components-to-chip/2.23-Modify-chip-options.ipynb",
             "tutorials/2 From components to chip/C. My first full quantum chip design/2.23 Modify chip options.ipynb"),
    '2.31': ("docs/tut/2-From-components-to-chip/2.31-Create-a-QComponent-Basic.ipynb",
             "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.31 Create a QComponent - Basic.ipynb"),
    '2.32': ("docs/tut/2-From-components-to-chip/2.32-Create-a-QComponent-Advanced.ipynb",
             "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.32 Create a QComponent - Advanced.ipynb"),
    '2.33': ("docs/tut/2-From-components-to-chip/2.33-Add-my-QComponent-to-a-reusable-python-file.ipynb",
             "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.33 Add my QComponent to a reusable python file.ipynb"),
    # --- Section 3 ---
    '3.1': ("docs/tut/3-Renderers/3.1-Introduction-to-QRenderers.ipynb",
            "tutorials/3 Renderers/3.1 Introduction to QRenderers.ipynb"),
    '3.2': ("docs/tut/3-Renderers/3.2-Export-your-design-to-GDS.ipynb",
            "tutorials/3 Renderers/3.2 Export your design to GDS.ipynb"),
    '3.3': ("docs/tut/3-Renderers/3.3-Render-your-design-to-Ansys.ipynb",
            "tutorials/3 Renderers/3.3 Render your design to Ansys.ipynb"),
    '3.4': ("docs/tut/3-Renderers/3.4-How-do-I-make-my-custom-QRenderer.ipynb",
            "tutorials/3 Renderers/3.4 How do I make my custom QRenderer.ipynb"),
    '3.5': ("docs/tut/3-Renderers/3.5-Render-your-design-to-Gmsh.ipynb",
            "tutorials/3 Renderers/3.5 Render your design to Gmsh.ipynb"),
    # --- Section 4 ---
    '4.01': ("docs/tut/4-Analysis/4.01-Capacitance-and-LOM.ipynb",
             "tutorials/4 Analysis/A. Core - EM and quantization/4.01 Capacitance and LOM.ipynb"),
    '4.02': ("docs/tut/4-Analysis/4.02-Eigenmode-and-EPR.ipynb",
             "tutorials/4 Analysis/A. Core - EM and quantization/4.02 Eigenmode and EPR.ipynb"),
    '4.03': ("docs/tut/4-Analysis/4.03-Impedance.ipynb",
             "tutorials/4 Analysis/A. Core - EM and quantization/4.03 Impedance.ipynb"),
    '4.04': ("docs/tut/4-Analysis/4.04-New-LOM-and-Fluxonium-Example.ipynb",
             "tutorials/4 Analysis/A. Core - EM and quantization/4.04 New LOM and Fluxonium Example.ipynb"),
    '4.05': ("docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example.ipynb",
             "tutorials/4 Analysis/A. Core - EM and quantization/4.05 New LOM and Two Coupled Transmon Example.ipynb"),
    '4.05s': ("docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example-with-sequence.ipynb",
              "tutorials/4 Analysis/A. Core - EM and quantization/4.05 New LOM and Two Coupled Transmon Example with sequence.ipynb"),
    '4.11': ("docs/tut/4-Analysis/4.11-Analyze-and-tune-a-transmon.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.11 Analyze and tune a transmon.ipynb"),
    '4.12': ("docs/tut/4-Analysis/4.12-Analyze-a-resonator.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.12 Analyze a resonator.ipynb"),
    '4.13': ("docs/tut/4-Analysis/4.13-Analyze-transmon-and-resonator.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.13 Analyze transmon and resonator.ipynb"),
    '4.14': ("docs/tut/4-Analysis/4.14-Analyze-a-double-hanger-resonator.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.14 Analyze a double hanger resonator (S Param).ipynb"),
    '4.15': ("docs/tut/4-Analysis/4.15-CPW-kappa-calculation.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.15 CPW kappa calculation.ipynb"),
    '4.16': ("docs/tut/4-Analysis/4.16-Analyze-S21-of-Hange-Geometry-with-WirebondLunchpadDriven.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.16 Analyze S21 of Hange Geometry with WirebondLunchpadDriven.ipynb"),
    '4.17': ("docs/tut/4-Analysis/4.17-Fit-S21-of-Hanger-Resonator-Geometry.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.17 Fit S21 of Hanger Resonator Geometry.ipynb"),
    '4.18': ("docs/tut/4-Analysis/4.18-Analyse-a-Resonator-with-Ports.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.18 Analyse a Resonator with Ports.ipynb"),
    '4.19': ("docs/tut/4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM.ipynb",
             "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.19 Analyze a transmon using ElmerFEM.ipynb"),
    '4.21': ("docs/tut/4-Analysis/4.21-Capacitance-matrix.ipynb",
             "tutorials/4 Analysis/C. Parametric sweeps/4.21 Capacitance matrix.ipynb"),
    '4.22': ("docs/tut/4-Analysis/4.22-Eigenmode-matrix.ipynb",
             "tutorials/4 Analysis/C. Parametric sweeps/4.22 Eigenmode matrix.ipynb"),
    '4.23': ("docs/tut/4-Analysis/4.23-Impedance-and-scattering-Z-S-Y-matrices.ipynb",
             "tutorials/4 Analysis/C. Parametric sweeps/4.23 Impedance and scattering Z S Y matrices.ipynb"),
    '4.31': ("docs/tut/4-Analysis/4.31-Plot-quantum-oscillator-wavefunction.ipynb",
             "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.31 Plot quantum oscillator wavefunction.ipynb"),
    '4.32': ("docs/tut/4-Analysis/4.32-Transmon-analytics-HCPB.ipynb",
             "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.32 Transmon analytics HCPB.ipynb"),
    '4.33': ("docs/tut/4-Analysis/4.33-Transmon-analytics.ipynb",
             "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.33 Transmon analytics.ipynb"),
    '4.34': ("docs/tut/4-Analysis/4.34-Transmon-qubit-CPB-hamiltonian-charge-basis.ipynb",
             "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.34 Transmon qubit CPB hamiltonian charge basis.ipynb"),
    'cqed': ("docs/tut/4-Analysis/cQED-with-the-Jaynes-Cummings-Interaction-Model.ipynb",
             "tutorials/4 Analysis/D. Hamiltonian models - after quantization/cQED with the Jaynes-Cummings Interaction Model.ipynb"),
    'cross': ("docs/tut/4-Analysis/Design-and-Simulation-of-a-Cross-Resonance-Gate.ipynb",
              "tutorials/4 Analysis/D. Hamiltonian models - after quantization/Design and Simulation of a Cross-Resonance Gate.ipynb"),
    # --- quick-topics (docs/tut/) / Appendix B (tutorials/) ---
    'qt_jj': ("docs/tut/quick-topics/JJ-Demo-Notebook.ipynb",
              "tutorials/Appendix B Quick topics/JJ Demo Notebook.ipynb"),
    'qt_pins': ("docs/tut/quick-topics/Managing-pins.ipynb",
                "tutorials/Appendix B Quick topics/Managing pins.ipynb"),
    'qt_vars': ("docs/tut/quick-topics/Managing-variables.ipynb",
                "tutorials/Appendix B Quick topics/Managing variables.ipynb"),
    'qt_open': ("docs/tut/quick-topics/Opening-documentation.ipynb",
                "tutorials/Appendix B Quick topics/Opening documentation.ipynb"),
    'qt_3fc': ("docs/tut/quick-topics/QComponent-3-fingers-capacitor.ipynb",
               "tutorials/Appendix B Quick topics/QComponent - 3-fingers capacitor.ipynb"),
    'qt_id': ("docs/tut/quick-topics/QComponent-Interdigitated-transmon.ipynb",
              "tutorials/Appendix B Quick topics/QComponent - Interdigitated transmon.ipynb"),
    'qt_over': ("docs/tut/quick-topics/Testing-QComponents-for-overlap-and-collisions.ipynb",
                "tutorials/Appendix B Quick topics/Testing QComponents for overlap and collisions.ipynb"),
}

# Per-notebook canonical choice (user-decided)
#   'tut'  → tutorials/ wins, copy → docs/tut/
#   'docs' → docs/tut/ wins, copy → tutorials/
CANONICAL = {
    # Section 1 — minor drift, docs/tut/ has the merged outputs + headless fixes
    '1.1': 'docs', '1.2': 'docs', '1.3': 'docs', '1.4': 'docs', '1.5': 'docs', '1.6': 'docs',
    # Section 2 — flip to 'tut' where tutorials/ is significantly larger
    # (rich outputs/images that source-match merge couldn't recover);
    # keep 'docs' where sizes are similar and merge worked
    '2.01': 'tut',                          # 74kB → 341kB
    '2.02': 'docs',                         # 72kB → 228kB (3x but small absolute)
    '2.11': 'tut', '2.12': 'tut',           # 179→764, 197→703
    '2.13': 'tut', '2.14': 'tut',           # 90→385, 108→305
    '2.21': 'tut', '2.22': 'tut',           # 185→427, 142→408
    '2.23': 'docs',                         # 69→17, docs LARGER
    '2.31': 'docs', '2.32': 'docs',         # 89→138, 95→139 (close)
    '2.33': 'tut',                          # 94→757 (8x)
    # Section 3 — user explicit
    '3.1': 'tut',  '3.2': 'tut',  '3.3': 'docs', '3.4': 'tut',  '3.5': 'tut',
    # Section 4 — user explicit: all docs
    '4.01': 'docs', '4.02': 'docs', '4.03': 'docs', '4.04': 'docs',
    '4.05': 'docs', '4.05s': 'docs',
    '4.11': 'docs', '4.12': 'docs', '4.13': 'docs', '4.14': 'docs',
    '4.15': 'docs', '4.16': 'docs', '4.17': 'docs', '4.18': 'docs', '4.19': 'docs',
    '4.21': 'docs', '4.22': 'docs', '4.23': 'docs',
    '4.31': 'docs', '4.32': 'docs', '4.33': 'docs', '4.34': 'docs',
    'cqed': 'docs', 'cross': 'docs',
    # quick-topics — docs/tut/ has the cleaner names; sync to Appendix B
    'qt_jj': 'docs', 'qt_pins': 'docs', 'qt_vars': 'docs', 'qt_open': 'docs',
    'qt_3fc': 'docs', 'qt_id': 'docs', 'qt_over': 'docs',
}


def file_size(p):
    try:
        return Path(p).stat().st_size
    except FileNotFoundError:
        return 0


def cells_match(a: Path, b: Path) -> bool:
    """Return True if two notebook files have identical full cell arrays.

    Matches the equality definition used by
    ``scripts/check_tutorials_sync.py`` (the canonical CI gate), which
    serializes the full ``cells`` array with ``json.dumps(..., sort_keys=True)``
    and compares. We include cell IDs, metadata, outputs — everything
    under ``cells`` — because diverging cell IDs between the two folders
    cause CI drift even when the user-visible source is identical.
    """
    try:
        with open(a) as fa, open(b) as fb:
            cells_a = json.load(fa).get("cells", [])
            cells_b = json.load(fb).get("cells", [])
    except (OSError, json.JSONDecodeError):
        return False

    return json.dumps(cells_a, sort_keys=True) == json.dumps(cells_b, sort_keys=True)


def main():
    write_mode = '--write' in sys.argv
    print(f"Mode: {'WRITE' if write_mode else 'DRY-RUN'}")
    print(f"{'key':<8} {'status':<10} {'choice':<6} {'src→dst':<8} {'src size':>9} {'dst size':>9}  notebook")
    print('-' * 105)

    tut_wins = 0
    docs_wins = 0
    in_sync = 0
    skipped = 0

    for key in sorted(PAIRS.keys()):
        docs_p, tut_p = PAIRS[key]
        if not Path(docs_p).exists():
            print(f"{key:<8} MISSING docs/tut: {docs_p}")
            skipped += 1
            continue
        if not Path(tut_p).exists():
            print(f"{key:<8} MISSING tutorials: {tut_p}")
            skipped += 1
            continue

        choice = CANONICAL.get(key, '?')
        if choice == 'tut':
            src, dst = tut_p, docs_p
            direction = 'tut→docs'
        elif choice == 'docs':
            src, dst = docs_p, tut_p
            direction = 'docs→tut'
        else:
            print(f"{key:<8} UNDECIDED — skipping")
            skipped += 1
            continue

        src_sz = file_size(src) // 1024
        dst_sz = file_size(dst) // 1024

        # Skip the actual copy when content already matches — saves
        # disk churn and gives an accurate "what would change" summary.
        already_in_sync = cells_match(Path(src), Path(dst))
        if already_in_sync:
            status = 'in-sync'
            in_sync += 1
        else:
            status = 'WILL COPY' if write_mode else 'would copy'
            if choice == 'tut':
                tut_wins += 1
            else:
                docs_wins += 1

        print(f"{key:<8} {status:<10} {choice:<6} {direction:<8} {src_sz:>6} kB {dst_sz:>6} kB  {Path(docs_p).name}")

        if write_mode and not already_in_sync:
            shutil.copyfile(src, dst)

    print('-' * 105)
    print(f"in-sync: {in_sync} | tut→docs: {tut_wins} | docs→tut: {docs_wins} | skipped: {skipped}")
    if not write_mode:
        if tut_wins == 0 and docs_wins == 0:
            print("\nNothing to do — all pairs are already in sync.")
        else:
            print("\nDry-run only. Re-run with --write to apply.")


if __name__ == '__main__':
    main()
