"""Sync notebooks between docs/tut/ and tutorials/ — direction picked automatically.

Usage:
  python3 _dev/sync_two_folders.py                # dry-run
  python3 _dev/sync_two_folders.py --write        # apply

How direction is chosen (per pair, in order):

  1. Cell content already identical → in-sync, no copy.
  2. Exactly one side differs from its HEAD blob → that side has the user's
     uncommitted edit. Copy it to the other side. This is the common case
     and means a user editing EITHER folder Just Works.
  3. Both sides differ from HEAD (both edited locally) → conflict. Falls
     back to the CANONICAL tiebreaker dict (defaults to 'tut' = user-facing
     root wins). Loud warning printed.
  4. Neither side differs from HEAD but the two files differ → HEAD itself
     is out of sync (rare; should have been caught by the CI sync gate at
     commit time). Picks whichever was committed more recently; CANONICAL
     breaks ties.

Net effect: a user editing ``tutorials/2.11 Routing 101.ipynb`` and running
``--write`` will see their edit propagate to ``docs/tut/`` — not overwritten.
Same in reverse for ``docs/tut/`` edits. CANONICAL only matters for the rare
"both-sides-edited" case.

After running, both folders contain identical cell content (just different
filenames: hyphenated in docs/tut/, spaces in tutorials/).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

# (docs/tut path, tutorials path) — every pair in sections 1, 2, 3, 4, quick-topics
PAIRS = {
    # --- Section 1 ---
    "1.1": (
        "docs/tut/1-Overview/1.1-Quick-start.ipynb",
        "tutorials/1 Overview/1.1 Quick start.ipynb",
    ),
    "1.2": (
        "docs/tut/1-Overview/1.2-Bird's-eye-view-of-Quantum-Metal.ipynb",
        "tutorials/1 Overview/1.2 Bird's eye view of Quantum Metal.ipynb",
    ),
    "1.3": (
        "docs/tut/1-Overview/1.3-Build-a-4-qubit-chip.ipynb",
        "tutorials/1 Overview/1.3 Build a 4-qubit chip.ipynb",
    ),
    "1.4": (
        "docs/tut/1-Overview/1.4-Saving-Your-Chip-Design.ipynb",
        "tutorials/1 Overview/1.4 Saving Your Chip Design.ipynb",
    ),
    "1.5": (
        "docs/tut/1-Overview/1.5-Parametric-design---iterate-and-compare.ipynb",
        "tutorials/1 Overview/1.5 Parametric design - iterate and compare.ipynb",
    ),
    # --- Section 2 ---
    "2.01": (
        "docs/tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent.ipynb",
        "tutorials/2 From components to chip/A. Using QComponents/2.01 How to use a QComponent.ipynb",
    ),
    "2.11": (
        "docs/tut/2-From-components-to-chip/2.11-Routing-101.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.11 Routing 101.ipynb",
    ),
    "2.12": (
        "docs/tut/2-From-components-to-chip/2.12-Simple-Meander.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.12 Simple Meander.ipynb",
    ),
    "2.13": (
        "docs/tut/2-From-components-to-chip/2.13-Hybrid-Auto-and-AStar.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.13 Hybrid Auto and AStar.ipynb",
    ),
    "2.14": (
        "docs/tut/2-From-components-to-chip/2.14-Get-them-all-with-MixedRoute.ipynb",
        "tutorials/2 From components to chip/B. Routing between QComponents/2.14 Get them all with MixedRoute.ipynb",
    ),
    "2.21": (
        "docs/tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip.ipynb",
        "tutorials/2 From components to chip/C. My first full quantum chip design/2.21 Design a 4 qubit full chip.ipynb",
    ),
    "2.22": (
        "docs/tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically.ipynb",
        "tutorials/2 From components to chip/C. My first full quantum chip design/2.22 Design 100 qubits programmatically.ipynb",
    ),
    "2.23": (
        "docs/tut/2-From-components-to-chip/2.23-Modify-chip-options.ipynb",
        "tutorials/2 From components to chip/C. My first full quantum chip design/2.23 Modify chip options.ipynb",
    ),
    "2.31": (
        "docs/tut/2-From-components-to-chip/2.31-Create-a-QComponent-Basic.ipynb",
        "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.31 Create a QComponent - Basic.ipynb",
    ),
    "2.32": (
        "docs/tut/2-From-components-to-chip/2.32-Create-a-QComponent-Advanced.ipynb",
        "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.32 Create a QComponent - Advanced.ipynb",
    ),
    "2.33": (
        "docs/tut/2-From-components-to-chip/2.33-Add-my-QComponent-to-a-reusable-python-file.ipynb",
        "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.33 Add my QComponent to a reusable python file.ipynb",
    ),
    # --- Section 3 ---
    "3.1": (
        "docs/tut/3-Renderers/3.1-Introduction-to-QRenderers.ipynb",
        "tutorials/3 Renderers/3.1 Introduction to QRenderers.ipynb",
    ),
    "3.2": (
        "docs/tut/3-Renderers/3.2-Export-your-design-to-GDS.ipynb",
        "tutorials/3 Renderers/3.2 Export your design to GDS.ipynb",
    ),
    "3.3": (
        "docs/tut/3-Renderers/3.3-Render-your-design-to-Ansys.ipynb",
        "tutorials/3 Renderers/3.3 Render your design to Ansys.ipynb",
    ),
    "3.4": (
        "docs/tut/3-Renderers/3.4-How-do-I-make-my-custom-QRenderer.ipynb",
        "tutorials/3 Renderers/3.4 How do I make my custom QRenderer.ipynb",
    ),
    "3.5": (
        "docs/tut/3-Renderers/3.5-Render-your-design-to-Gmsh.ipynb",
        "tutorials/3 Renderers/3.5 Render your design to Gmsh.ipynb",
    ),
    # --- Section 4 ---
    "4.01": (
        "docs/tut/4-Analysis/4.01-Capacitance-and-LOM.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.01 Capacitance and LOM.ipynb",
    ),
    "4.02": (
        "docs/tut/4-Analysis/4.02-Eigenmode-and-EPR.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.02 Eigenmode and EPR.ipynb",
    ),
    "4.03": (
        "docs/tut/4-Analysis/4.03-Impedance.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.03 Impedance.ipynb",
    ),
    "4.04": (
        "docs/tut/4-Analysis/4.04-New-LOM-and-Fluxonium-Example.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.04 New LOM and Fluxonium Example.ipynb",
    ),
    "4.05": (
        "docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.05 New LOM and Two Coupled Transmon Example.ipynb",
    ),
    "4.05s": (
        "docs/tut/4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example-with-sequence.ipynb",
        "tutorials/4 Analysis/A. Core - EM and quantization/4.05 New LOM and Two Coupled Transmon Example with sequence.ipynb",
    ),
    "4.11": (
        "docs/tut/4-Analysis/4.11-Analyze-and-tune-a-transmon.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.11 Analyze and tune a transmon.ipynb",
    ),
    "4.12": (
        "docs/tut/4-Analysis/4.12-Analyze-a-resonator.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.12 Analyze a resonator.ipynb",
    ),
    "4.13": (
        "docs/tut/4-Analysis/4.13-Analyze-transmon-and-resonator.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.13 Analyze transmon and resonator.ipynb",
    ),
    "4.14": (
        "docs/tut/4-Analysis/4.14-Analyze-a-double-hanger-resonator.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.14 Analyze a double hanger resonator (S Param).ipynb",
    ),
    "4.15": (
        "docs/tut/4-Analysis/4.15-CPW-kappa-calculation.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.15 CPW kappa calculation.ipynb",
    ),
    "4.16": (
        "docs/tut/4-Analysis/4.16-Analyze-S21-of-Hange-Geometry-with-WirebondLunchpadDriven.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.16 Analyze S21 of Hange Geometry with WirebondLunchpadDriven.ipynb",
    ),
    "4.17": (
        "docs/tut/4-Analysis/4.17-Fit-S21-of-Hanger-Resonator-Geometry.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.17 Fit S21 of Hanger Resonator Geometry.ipynb",
    ),
    "4.18": (
        "docs/tut/4-Analysis/4.18-Analyse-a-Resonator-with-Ports.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.18 Analyse a Resonator with Ports.ipynb",
    ),
    "4.19": (
        "docs/tut/4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM.ipynb",
        "tutorials/4 Analysis/B. Advanced - Direct use of the renderers/4.19 Analyze a transmon using ElmerFEM.ipynb",
    ),
    "4.21": (
        "docs/tut/4-Analysis/4.21-Capacitance-matrix.ipynb",
        "tutorials/4 Analysis/C. Parametric sweeps/4.21 Capacitance matrix.ipynb",
    ),
    "4.22": (
        "docs/tut/4-Analysis/4.22-Eigenmode-matrix.ipynb",
        "tutorials/4 Analysis/C. Parametric sweeps/4.22 Eigenmode matrix.ipynb",
    ),
    "4.23": (
        "docs/tut/4-Analysis/4.23-Impedance-and-scattering-Z-S-Y-matrices.ipynb",
        "tutorials/4 Analysis/C. Parametric sweeps/4.23 Impedance and scattering Z S Y matrices.ipynb",
    ),
    "4.31": (
        "docs/tut/4-Analysis/4.31-Plot-quantum-oscillator-wavefunction.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.31 Plot quantum oscillator wavefunction.ipynb",
    ),
    "4.32": (
        "docs/tut/4-Analysis/4.32-Transmon-analytics-HCPB.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.32 Transmon analytics HCPB.ipynb",
    ),
    "4.33": (
        "docs/tut/4-Analysis/4.33-Transmon-analytics.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.33 Transmon analytics.ipynb",
    ),
    "4.34": (
        "docs/tut/4-Analysis/4.34-Transmon-qubit-CPB-hamiltonian-charge-basis.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/4.34 Transmon qubit CPB hamiltonian charge basis.ipynb",
    ),
    "cqed": (
        "docs/tut/4-Analysis/cQED-with-the-Jaynes-Cummings-Interaction-Model.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/cQED with the Jaynes-Cummings Interaction Model.ipynb",
    ),
    "cross": (
        "docs/tut/4-Analysis/Design-and-Simulation-of-a-Cross-Resonance-Gate.ipynb",
        "tutorials/4 Analysis/D. Hamiltonian models - after quantization/Design and Simulation of a Cross-Resonance Gate.ipynb",
    ),
    # --- quick-topics (docs/tut/) / Appendix B (tutorials/) ---
    "qt_jj": (
        "docs/tut/quick-topics/JJ-Demo-Notebook.ipynb",
        "tutorials/Appendix B Quick topics/JJ Demo Notebook.ipynb",
    ),
    "qt_pins": (
        "docs/tut/quick-topics/Managing-pins.ipynb",
        "tutorials/Appendix B Quick topics/Managing pins.ipynb",
    ),
    "qt_vars": (
        "docs/tut/quick-topics/Managing-variables.ipynb",
        "tutorials/Appendix B Quick topics/Managing variables.ipynb",
    ),
    "qt_open": (
        "docs/tut/quick-topics/Opening-documentation.ipynb",
        "tutorials/Appendix B Quick topics/Opening documentation.ipynb",
    ),
    "qt_3fc": (
        "docs/tut/quick-topics/QComponent-3-fingers-capacitor.ipynb",
        "tutorials/Appendix B Quick topics/QComponent - 3-fingers capacitor.ipynb",
    ),
    "qt_id": (
        "docs/tut/quick-topics/QComponent-Interdigitated-transmon.ipynb",
        "tutorials/Appendix B Quick topics/QComponent - Interdigitated transmon.ipynb",
    ),
    "qt_over": (
        "docs/tut/quick-topics/Testing-QComponents-for-overlap-and-collisions.ipynb",
        "tutorials/Appendix B Quick topics/Testing QComponents for overlap and collisions.ipynb",
    ),
}

# Per-pair CONFLICT TIEBREAKER (only consulted when both sides edited locally
# or HEAD itself is drifted with equal commit times).
#
#   'tut'  → tutorials/ wins (user-facing root; this is the default)
#   'docs' → docs/tut/ wins
#
# Empty / not listed → default 'tut'. We deliberately keep this dict empty:
# the algorithm's "exactly-one-side-dirty" path covers virtually every real
# scenario, so a CANONICAL override would be wrong (it would silently
# clobber a user edit). Add entries here ONLY if you have a long-running
# reason that docs/tut/ should win when both sides are edited.
CANONICAL: dict[str, str] = {}
DEFAULT_TIEBREAKER = "tut"


def file_size(p):
    try:
        return Path(p).stat().st_size
    except FileNotFoundError:
        return 0


def _cells_from_text(text: str):
    try:
        return json.loads(text).get("cells", [])
    except json.JSONDecodeError:
        return None


def _cells_canonical(cells) -> str | None:
    if cells is None:
        return None
    return json.dumps(cells, sort_keys=True)


def cells_match(a: Path, b: Path) -> bool:
    """Return True if two notebook files have identical full cell arrays.

    Matches the equality definition used by
    ``scripts/check_tutorials_sync.py`` (the CI gate). Cell IDs, metadata,
    outputs — everything under ``cells`` — counts: diverging cell IDs
    cause CI drift even when the user-visible source is identical.
    """
    try:
        a_cells = _cells_canonical(_cells_from_text(a.read_text()))
        b_cells = _cells_canonical(_cells_from_text(b.read_text()))
    except OSError:
        return False
    return a_cells is not None and a_cells == b_cells


def matches_head_blob(path: Path) -> bool:
    """True if the working-tree file's cells match the HEAD blob's cells.

    Returns False if path is untracked (not in HEAD) — meaning "has
    uncommitted state vs HEAD." Also False if either side fails to parse.
    """
    try:
        head_text = subprocess.run(
            ["git", "show", f"HEAD:{path}"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout
    except subprocess.CalledProcessError:
        return False  # not tracked at HEAD → counts as "dirty"
    head_cells = _cells_canonical(_cells_from_text(head_text))
    try:
        wt_cells = _cells_canonical(_cells_from_text(path.read_text()))
    except OSError:
        return False
    return head_cells is not None and head_cells == wt_cells


def last_commit_time(path: Path) -> int:
    """Unix committer-time of the last commit touching ``path``. 0 if untracked."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(path)],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        return int(out) if out else 0
    except (subprocess.CalledProcessError, ValueError):
        return 0


def pick_direction(key: str, docs_p: Path, tut_p: Path):
    """Decide which side to copy FROM. Returns (src, dst, label, reason)."""
    docs_dirty = not matches_head_blob(docs_p)
    tut_dirty = not matches_head_blob(tut_p)

    if docs_dirty and not tut_dirty:
        return docs_p, tut_p, "docs→tut", "docs/tut/ edited"
    if tut_dirty and not docs_dirty:
        return tut_p, docs_p, "tut→docs", "tutorials/ edited"

    if docs_dirty and tut_dirty:
        choice = CANONICAL.get(key, DEFAULT_TIEBREAKER)
        if choice == "docs":
            return docs_p, tut_p, "docs→tut", "BOTH edited — CANONICAL=docs"
        return tut_p, docs_p, "tut→docs", "BOTH edited — default tut"

    # Neither dirty vs HEAD, but cells_match was False → HEAD itself drifted.
    docs_t = last_commit_time(docs_p)
    tut_t = last_commit_time(tut_p)
    if docs_t > tut_t:
        return docs_p, tut_p, "docs→tut", f"HEAD drift; docs newer ({docs_t}>{tut_t})"
    if tut_t > docs_t:
        return tut_p, docs_p, "tut→docs", f"HEAD drift; tut newer ({tut_t}>{docs_t})"
    choice = CANONICAL.get(key, DEFAULT_TIEBREAKER)
    if choice == "docs":
        return docs_p, tut_p, "docs→tut", "HEAD drift; equal times; CANONICAL=docs"
    return tut_p, docs_p, "tut→docs", "HEAD drift; equal times; default tut"


def main():
    write_mode = "--write" in sys.argv
    print(f"Mode: {'WRITE' if write_mode else 'DRY-RUN'}")
    print(
        f"{'key':<8} {'status':<10} {'dir':<8} {'src size':>9} {'dst size':>9}  reason / notebook"
    )
    print("-" * 110)

    tut_wins = 0
    docs_wins = 0
    in_sync = 0
    conflict = 0
    skipped = 0

    for key in sorted(PAIRS.keys()):
        docs_p_s, tut_p_s = PAIRS[key]
        docs_p, tut_p = Path(docs_p_s), Path(tut_p_s)
        if not docs_p.exists():
            print(f"{key:<8} MISSING docs/tut: {docs_p}")
            skipped += 1
            continue
        if not tut_p.exists():
            print(f"{key:<8} MISSING tutorials: {tut_p}")
            skipped += 1
            continue

        if cells_match(docs_p, tut_p):
            print(
                f"{key:<8} {'in-sync':<10} {'-':<8} "
                f"{file_size(docs_p) // 1024:>6} kB {file_size(tut_p) // 1024:>6} kB  "
                f"{docs_p.name}"
            )
            in_sync += 1
            continue

        src, dst, direction, reason = pick_direction(key, docs_p, tut_p)
        status = "WILL COPY" if write_mode else "would copy"
        if "BOTH" in reason:
            conflict += 1
            status = "CONFLICT" if write_mode else "conflict"
        if direction == "tut→docs":
            tut_wins += 1
        else:
            docs_wins += 1

        print(
            f"{key:<8} {status:<10} {direction:<8} "
            f"{file_size(src) // 1024:>6} kB {file_size(dst) // 1024:>6} kB  "
            f"{reason}  ({docs_p.name})"
        )

        if write_mode:
            shutil.copyfile(src, dst)

    print("-" * 110)
    print(
        f"in-sync: {in_sync} | tut→docs: {tut_wins} | docs→tut: {docs_wins} | "
        f"conflicts: {conflict} | skipped: {skipped}"
    )
    if conflict:
        print(
            f"\n⚠  {conflict} pair(s) had edits on BOTH sides. The tiebreaker was "
            "applied (see reason column). Inspect the result; if it picked the "
            "wrong side, revert that file from git and re-run."
        )
    if not write_mode:
        if tut_wins == 0 and docs_wins == 0:
            print("\nNothing to do — all pairs are already in sync.")
        else:
            print("\nDry-run only. Re-run with --write to apply.")


if __name__ == "__main__":
    main()
