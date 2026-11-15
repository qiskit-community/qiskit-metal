"""Build, check, export and analyze a one-qubit chip without a GUI.

Run it with ``python headless_chip.py chip_out``. It needs only the lite
install (``pip install quantum-metal``). Set ``SOURCE_DATE_EPOCH`` to get a
GDS file that is identical from run to run.
"""

import hashlib
import sys
from pathlib import Path

import qiskit_metal as qm
from qiskit_metal import designs
from qiskit_metal.analyses.hamiltonian.transmon_charge_basis import Hcpb
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.validation import validate


def build(resonator_length="6.0mm"):
    """Return a fresh design: a transmon, a launchpad and a meandered resonator."""
    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    design.chips.main.size.size_x = "4mm"
    design.chips.main.size.size_y = "3mm"

    TransmonPocket(
        design,
        "Q1",
        options=dict(
            pos_x="-1.0mm",
            pos_y="0.0mm",
            connection_pads=dict(readout=dict(loc_W=+1, loc_H=+1, pad_gap="15um")),
        ),
    )
    LaunchpadWirebond(
        design, "LP1", options=dict(pos_x="1.6mm", pos_y="0.8mm", orientation="180")
    )
    RouteMeander(
        design,
        "readout",
        options=dict(
            pin_inputs=dict(
                start_pin=dict(component="Q1", pin="readout"),
                end_pin=dict(component="LP1", pin="tie"),
            ),
            total_length=resonator_length,
            fillet="90um",
            lead=dict(start_straight="0.3mm"),
        ),
    )
    return design


def fingerprint(design):
    """A short hash of every polygon and path in the design, in a fixed order."""
    h = hashlib.sha256()
    for kind, table in sorted(design.qgeometry.tables.items()):
        for _, row in table.sort_values(["component", "name"]).iterrows():
            h.update(
                f"{kind}|{row['component']}|{row['name']}|{row['geometry'].wkt}".encode()
            )
    return h.hexdigest()[:16]


def main(out_dir="chip_out"):
    out = Path(out_dir)
    out.mkdir(exist_ok=True)

    design = build()

    # 1. Check. ERROR findings mean the geometry is wrong; raise on them.
    result = validate(design)
    print(result.report())
    result.raise_if_errors()

    # 2. Export: a picture for review and the mask for the fab.
    qm.view(design).savefig(out / "chip.png", dpi=150)
    design.renderers.gds.export_to_gds(str(out / "chip.gds"))

    # 3. Analyze. Without a field solver, a transmon level estimate from Ej, Ec.
    spectrum = Hcpb(nlevels=15, Ej=13000.0, Ec=300.0, ng=0.0)  # MHz
    f01, f12 = spectrum.fij(0, 1), spectrum.fij(1, 2)
    print(f"f01 = {f01 / 1000:.3f} GHz, anharmonicity = {f12 - f01:.0f} MHz")

    print("geometry fingerprint:", fingerprint(design))
    return out


if __name__ == "__main__":
    main(*sys.argv[1:])
