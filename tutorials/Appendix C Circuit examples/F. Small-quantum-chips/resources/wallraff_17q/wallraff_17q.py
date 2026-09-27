"""Layout of the ETH Zurich 17-qubit distance-3 surface-code device.

Device: S. Krinner, N. Lacroix et al., "Realizing repeated quantum error
correction in a distance-three surface code", Nature 605, 669 (2022).
Geometry: measured from published micrographs of the die; see the ``_source``
field of ``geometry.json`` beside this file. Nothing below is invented; where a
value is chosen rather than measured, the comment says why.

Build in stages -- the tutorial notebook runs them one at a time::

    design = new_design()
    for title, stage in STAGES:
        stage(design)

or all at once with :func:`build`.

Component names
---------------
Qubits keep the paper's labels (D1-D9, X1-X4, Z1-Z4). Lines are
``<ROLE>_<qubit>`` (``FLUX_D5``, ``DRIVE_D5``, ``RO_D5``, ``PURCELL_D5``),
lattice couplers ``CPL_<a>_<b>``, feedlines ``FEED_<group>`` /
``FEEDIN_<group>`` (either side of the input capacitor), with ``_1``, ``_2``
... for the pieces between airbridges. Launchpads are ``LP_<role>_<qubit>``,
``LP_feed_<group>_<edge>`` or ``LP_spare_<edge>_<slot>``. Airbridges are
``AB*_<line>_<k>``; capacitors ``FEEDCAP_<group>``, ``PUCAP_<qubit>``,
``RPCAP_<qubit>``; terminations ``FLUXSHORT_``, ``DRIVEOPEN_``, ``ROSHORT_``,
``PUSHORT_``.
"""

import json
import math
import os

import numpy as np
from shapely.geometry import LineString, Point

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.lumped.cap_finger_in_frame import CapFingerInFrame
from qiskit_metal.qlibrary.lumped.cap_n_interdigital import CapNInterdigital
from qiskit_metal.qlibrary.qubits.star_qubit import StarQubit
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.terminations.short_to_ground import ShortToGround
from qiskit_metal.qlibrary.tlines.airbridge import Airbridge
from qiskit_metal.qlibrary.tlines.polyline_cpw import PolylineCPW

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "geometry.json")) as _f:
    DATA = json.load(_f)

# --- measured and derived constants ------------------------------------------
AX, AY = DATA["lattice_mm"]["x"], DATA["lattice_mm"]["y"]
DIE = DATA["die_mm"]
RING = DATA["pad_necking_mm"]  # launchpads are positioned by their necking point

# CPW. Measured beside the feedline input capacitors: center conductor + one gap
# = 14.0 +- 1.5 um; the image cannot separate the two. 50 ohm on silicon needs
# w/(w + 2g) ~ 0.44, which with w + g = 14 um gives w ~ 8.5, g ~ 5.5 um.
CPW = {"width": "8.5um", "gap": "5.5um"}

PAD = dict(pad_width="170um", pad_height="230um", pad_gap="70um", taper_height="240um")

# StarQubit scaled to the measured island: ~0.32 mm etched pocket, so an outer
# radius of ~160 um; the rest of the default geometry scaled by 160/300.
STAR = dict(
    radius="160um",
    center_radius="53um",
    gap_couplers="13um",
    gap_readout="6um",
    connector_length="40um",
    trap_offset="11um",
    junc_h="53um",
    number_of_connectors="4",
    resolution="16",
)

# Lattice cell of each qubit (col, row); D5 at the origin.
QUBITS = {
    "Z1": (-1, 2),
    "D1": (0, 2),
    "D4": (-1, 1),
    "X2": (0, 1),
    "D2": (1, 1),
    "X1": (2, 1),
    "D7": (-2, 0),
    "Z2": (-1, 0),
    "D5": (0, 0),
    "Z3": (1, 0),
    "D3": (2, 0),
    "X4": (-2, -1),
    "D8": (-1, -1),
    "X3": (0, -1),
    "D6": (1, -1),
    "D9": (0, -2),
    "Z4": (1, -2),
}
CELL = {v: k for k, v in QUBITS.items()}
# Qubit centers on the regular lattice. The traced centers (DATA["qubits"])
# scatter about these by up to ~50 um -- a few pixels of tracing noise -- so
# every distance from a qubit is measured from where the qubit is drawn.
QUBIT_POS = {q: np.array([col * AX, row * AY]) for q, (col, row) in QUBITS.items()}
GROUPS = DATA["readout_groups"]
GROUP = {q: g for g, v in GROUPS.items() for q in v["qubits"]}
RO_ARM = {q: v["arm"] for v in GROUPS.values() for q in v["qubits"]}  # x 45 deg

EDGE_LETTER = {"top": "N", "bot": "S", "left": "W", "right": "E"}
INWARD = {"top": "270", "bot": "90", "left": "0", "right": "180"}
ARM_PIN = {0: "pin_cpl1", 2: "pin_cpl2", 4: "pin_cpl3", 6: "pin_cpl4"}

LINES = DATA["lines"]
FLUX_QUBIT = {v: k for k, v in LINES["flux"]["pad"].items()}  # pad slot -> qubit
DRIVE_QUBIT = {v: k for k, v in LINES["drive"]["pad"].items()}

# Traced lines are resampled to a uniform arclength step. Round a tight bend the
# chord between samples is shorter than the step (38 um minimum here), so
# min_segment must sit below that -- otherwise PolylineCPW drops a vertex and the
# chord cuts the bend -- and the fillet must fit within half of it, since
# PolylineCPW clamps the fillet to half its shortest segment.
TRACE_STEP = 0.045
TRACE_MIN_SEG = "30um"
TRACE_FILLET = "15um"

# Where a line meets a pin it leaves straight along the pin's normal for LEAD
# before following the trace, so the CPW meets the pad square-on and its end
# is flush with it.
LEAD = 0.04

# StarQubit's connector pins sit 0.20 mm from the qubit center.
PIN_R = 0.21
# Where the control lines stop, from the qubit center: the flux short sits at
# the pocket edge beside the SQUID (measured 0.165-0.21 mm; the pocket is
# 0.20 mm and StarQubit's junction reaches 0.2105 mm, so 0.215 clears it);
# the drive line stops further out (measured 0.23-0.29 mm).
FLUX_STANDOFF = 0.215
DRIVE_STANDOFF = 0.28

CAPS = DATA["capacitors"]
_G = CAPS["assumed_gap_um"] / 1000
CELL_W = CAPS["finger_in_frame_cell"]["outer_width_um"] / 1000 - _G
CELL_TRACE = CAPS["finger_in_frame_cell"]["frame_trace_centerline_um"] / 1000 - _G
INPUT_CAP_L = CAPS["input_caps"]["outer_length_um"] / 1000 - _G
FEED_TO_FRAME = (
    CAPS["purcell_couplers"]["feed_to_frame_gap_centerline_um"] / 1000 + _G / 2
)
RP = CAPS["readout_purcell_coupler"]


# --- small geometry helpers ---------------------------------------------------
def arm_rotation(deg):
    """Compass angle for a StarQubit arm -> its ``rotation_*`` option.

    StarQubit places each connector's pin 90 deg behind its rotation option
    (rotation R puts the pin at R - 90).
    """
    return f"{(deg + 90) % 360}"


def qubit_frame(q):
    """``(flux_axis_deg, side)`` for qubit ``q``, from the traced lines.

    The flux line ends on one of the lattice axes, beside the SQUID; the
    readout arm is on a diagonal 45 degrees to one side of it. ``side`` is +1
    when the readout is counter-clockwise from the flux axis, -1 otherwise.
    """
    path = [np.array(p) for p in LINES["flux"]["path"][q]]
    end = trim_to_standoff(path, QUBIT_POS[q], FLUX_STANDOFF)[-1] - QUBIT_POS[q]
    axis = round(math.degrees(math.atan2(end[1], end[0])) / 90) * 90 % 360
    side = {45: 1, 315: -1}[(RO_ARM[q] * 45 - axis) % 360]
    return axis, side


# The device qubit (Krinner et al. 2022; close-up in the Wallraff slides) has
# five pads spaced about 72 degrees -- the readout and four couplers -- and the
# SQUID on the island arm between the readout pad and a coupler pad. Measured
# with the SQUID at 0: readout 42, couplers 112, 180, 252, 325. Taken here as
# the regular pattern: readout at +36, couplers at -36, +108, 180, -108 (times
# ``side``). The coupler at -36 serves the neighbor on the flux axis; the pad
# angle differs from the neighbor's direction, which is why its line jogs.
READOUT_PAD = 36
COUPLER_PAD = {0: -36, 90: 108, 180: 180, 270: 252}  # neighbor direction -> pad


def pad_angles(q):
    """Compass angles of qubit ``q``'s pads and junction.

    Returns ``{"cpl": {cardinal_arm_deg: pad_deg}, "rdout": deg, "jj": deg}``.
    """
    axis, side = qubit_frame(q)
    cpl = {}
    for arm in (0, 90, 180, 270):
        rel = (side * (arm - axis)) % 360
        cpl[arm] = (axis + side * COUPLER_PAD[rel]) % 360
    return {"cpl": cpl, "rdout": (axis + side * READOUT_PAD) % 360, "jj": axis}


def slot_tag(v):
    """+2.5 -> 'p2_5', -3.5 -> 'm3_5'."""
    return ("p" if v >= 0 else "m") + f"{abs(v):.1f}".replace(".", "_")


def bonds():
    """The 24 lattice bonds as (qubit_a, qubit_b, arm_of_a), each once."""
    out = []
    for name, (c, r) in QUBITS.items():
        for (dc, dr), arm in (((1, 0), 0), ((0, 1), 2)):
            if (c + dc, r + dr) in CELL:
                out.append((name, CELL[(c + dc, r + dr)], arm))
    return out


def resample(poly, step):
    """Uniform arclength resampling, endpoints kept."""
    P = np.asarray(poly, float)
    d = np.linalg.norm(np.diff(P, axis=0), axis=1)
    t = np.concatenate([[0], np.cumsum(d)])
    n = max(int(np.floor(t[-1] / step)), 1)
    tt = np.linspace(0, t[-1], n + 1)
    return np.stack([np.interp(tt, t, P[:, 0]), np.interp(tt, t, P[:, 1])], 1)


def dist_to_polyline(p, P):
    a, b = P[:-1], P[1:]
    ab = b - a
    t = np.clip(((p - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
    return float(np.linalg.norm(a + t[:, None] * ab - p, axis=1).min())


def project(line, p):
    """Nearest point on polyline ``line`` to ``p``: (point, arclength, tangent)."""
    a, b = line[:-1], line[1:]
    ab = b - a
    t = np.clip(((p - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
    feet = a + t[:, None] * ab
    i = int(np.linalg.norm(feet - p, axis=1).argmin())
    seglen = np.linalg.norm(ab, axis=1)
    return feet[i], seglen[:i].sum() + t[i] * seglen[i], ab[i] / max(seglen[i], 1e-12)


def trim_to_standoff(pts, center, standoff):
    """Cut a polyline where it crosses a circle of ``standoff`` about ``center``.

    Interpolates on the crossing segment, so the final approach direction is
    kept.
    """
    pts = list(pts)
    while len(pts) > 2 and np.linalg.norm(pts[-2] - center) < standoff:
        pts.pop()
    a, b = pts[-2], pts[-1]
    seg = b - a
    A, B = seg @ seg, 2 * seg @ (a - center)
    C = (a - center) @ (a - center) - standoff**2
    disc = B * B - 4 * A * C
    if disc >= 0 and A > 0:
        roots = [
            r for r in ((-B - disc**0.5) / (2 * A), (-B + disc**0.5) / (2 * A)) if r > 0
        ]
        if roots:
            pts[-1] = a + seg * min(max(min(roots), 0.0), 1.0)
    return pts


def join_pin(pts, pin, normal, at="start"):
    """Join a traced line to a pin by following the trace.

    Drops traced points not yet ahead of the pin along its outward normal
    (the traced stroke runs over pads and islands), then starts at the pin.
    """
    pin, normal = np.asarray(pin, float), np.asarray(normal, float)
    seq = [np.asarray(p, float) for p in (pts if at == "start" else list(pts)[::-1])]
    while len(seq) > 2 and (seq[0] - pin) @ normal < TRACE_STEP / 2:
        seq.pop(0)
    seq = [pin] + seq
    return seq if at == "start" else seq[::-1]


def join_pad(pts, lp, at="start"):
    return join_pin(pts, lp.pins["tie"]["middle"], lp.pins["tie"]["normal"], at=at)


def owner_of_pin(design, base, pin):
    """Name of the piece of line ``base`` (base, base_1, ...) carrying ``pin``."""
    for n, c in design.components.items():
        if (n == base or n.startswith(base + "_")) and pin in c.pins:
            return n
    return None


def _substring(line, a, b):
    """Vertices of ``line`` between arclengths a and b, endpoints included."""
    if b - a < 0.02:
        return None
    pts = [np.array(line.interpolate(a).coords[0])]
    acc = 0.0
    coords = list(line.coords)
    for p0, p1 in zip(coords[:-1], coords[1:]):
        seg = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
        if a < acc + seg and acc > a and acc < b:
            pts.append(np.array(p0))
        acc += seg
    pts.append(np.array(line.interpolate(b).coords[0]))
    return pts


def split_at_crossings(design, pts, name, over, tag, clear=0.055):
    """Cut a line where it crosses an earlier one and bridge each cut.

    Returns the line as an ordered list of ("seg", points) and ("bridge",
    component name). The upper line is interrupted for ``2 * clear`` and an
    ``Airbridge`` spans the gap on its own layer; :func:`draw_traced` wires the
    cut ends to the bridge's pins ``a``/``b``.
    """
    others = []
    tbl = design.qgeometry.tables["path"]
    for cname, comp in design.components.items():
        if cname.startswith(tuple(over)):
            rows = tbl[(tbl["component"] == comp.id) & (~tbl["subtract"])]
            others += [r.geometry for _, r in rows.iterrows()]
    line = LineString([tuple(p) for p in pts])
    hits = []
    for o in others:
        inter = line.intersection(o)
        for g in [] if inter.is_empty else getattr(inter, "geoms", [inter]):
            hits.append(line.project(Point(g.centroid)))
    items, prev = [], 0.0
    for k, d in enumerate(sorted(hits)):
        seg = _substring(line, prev, d - clear)
        if seg is not None:
            items.append(("seg", seg))
        p = line.interpolate(d)
        nxt = line.interpolate(min(d + 0.01, line.length))
        bname = f"{tag}_{name}_{k}"
        Airbridge(
            design,
            bname,
            options=dict(
                pos_x=f"{p.x}mm",
                pos_y=f"{p.y}mm",
                orientation=f"{math.degrees(math.atan2(nxt.y - p.y, nxt.x - p.x))}",
                crossover_length=f"{2 * clear * 1000}um",
            ),
        )
        items.append(("bridge", bname))
        prev = d + clear
    seg = _substring(line, prev, line.length)
    if seg is not None:
        items.append(("seg", seg))
    if not items or items[0][0] != "seg" or items[-1][0] != "seg":
        raise ValueError(f"{name}: a crossing sits within {clear} mm of a line end")
    return items


def pin_at(design, p, tol=1e-6):
    """``(middle, normal)`` of the component pin at point ``p``, if any.

    Lines and bridges are skipped: only pins a line is drawn *to* count.
    """
    for comp in design.components.values():
        if isinstance(comp, (PolylineCPW, Airbridge)):
            continue
        for pin in comp.pins.values():
            if np.linalg.norm(np.asarray(pin["middle"]) - p) < tol:
                return np.asarray(pin["middle"], float), np.asarray(
                    pin["normal"], float
                )
    return None


def with_lead(P, pin, normal, at="start"):
    """Start (or end) resampled points ``P`` with a straight lead off a pin.

    The lead runs LEAD along the pin's outward normal; points within reach of
    its tip are dropped (by distance, so a sideways jog near the pin is kept),
    and the line then carries on along the trace.
    """
    seq = [np.asarray(q, float) for q in (P if at == "start" else list(P)[::-1])]
    tip = pin + normal * LEAD
    rest = seq[1:]
    while len(rest) > 1 and np.linalg.norm(rest[0] - pin) < LEAD + TRACE_STEP / 2:
        rest.pop(0)
    seq = [pin, tip] + rest
    return seq if at == "start" else seq[::-1]


def draw_traced(design, name, pts, over, tag, taps=None):
    """Draw a traced line as PolylineCPW pieces, bridged and fully wired.

    ``taps`` ({pin_name: [x, y]}) become PolylineCPW taps on whichever piece
    lies nearest each target, for branches off the middle of the line.
    Returns the piece names, first to last.
    """
    items = split_at_crossings(design, pts, name, over, tag)
    pieces = [v for kind, v in items if kind == "seg"]
    owner = {
        tn: min(
            range(len(pieces)),
            key=lambda i: dist_to_polyline(
                np.asarray(tgt, float), np.asarray(pieces[i], float)
            ),
        )
        for tn, tgt in (taps or {}).items()
    }
    names, chain, i = [], [], 0
    for k, (kind, v) in enumerate(items):
        if kind == "bridge":
            chain.append(("bridge", v))
            continue
        n = name + (f"_{i}" if i else "")
        v = resample(v, TRACE_STEP)
        if k > 0:  # after a bridge: leave its pin b along the bridge axis
            b = design.components[items[k - 1][1]].pins["b"]
            v = with_lead(v, np.asarray(b["middle"]), np.asarray(b["normal"]), "start")
        elif (hit := pin_at(design, v[0])) is not None:
            v = with_lead(v, *hit, "start")
        if k < len(items) - 1:  # before a bridge: arrive at its pin a
            a = design.components[items[k + 1][1]].pins["a"]
            v = with_lead(v, np.asarray(a["middle"]), np.asarray(a["normal"]), "end")
        elif (hit := pin_at(design, v[-1])) is not None:
            v = with_lead(v, *hit, "end")
        PolylineCPW(
            design,
            n,
            options=dict(
                taps=Dict(
                    {
                        tn: list(map(float, taps[tn]))
                        for tn, j in owner.items()
                        if j == i
                    }
                ),
                points=[list(map(float, p)) for p in v],
                trace_width=CPW["width"],
                trace_gap=CPW["gap"],
                fillet=TRACE_FILLET,
                min_segment=TRACE_MIN_SEG,
            ),
        )
        names.append(n)
        chain.append(("seg", n))
        i += 1
    for (k1, n1), (k2, n2) in zip(chain[:-1], chain[1:]):
        design.connect_pins(
            design.components[n1].id,
            "end" if k1 == "seg" else "b",
            design.components[n2].id,
            "start" if k2 == "seg" else "a",
        )
    return names


def terminate(design, name, cls, pts, seg, at):
    """Open or short one end of a line and register the net.

    ``orientation`` is the line's outgoing direction at that end; the
    termination's pin then faces back into the line.
    """
    a, b = (pts[0], pts[1]) if at == "start" else (pts[-1], pts[-2])
    out = a - b
    t = cls(
        design,
        name,
        options=dict(
            pos_x=f"{a[0]}mm",
            pos_y=f"{a[1]}mm",
            orientation=f"{math.degrees(math.atan2(out[1], out[0])) % 360}",
            width=CPW["width"],
            **({"gap": CPW["gap"]} if cls is OpenToGround else {}),
        ),
    )
    design.connect_pins(
        design.components[seg].id, at, t.id, "short" if cls is ShortToGround else "open"
    )
    return t


# --- stages -------------------------------------------------------------------
def new_design():
    """An empty planar design with the measured die size."""
    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    design.chips.main.size.size_x = f"{DIE}mm"
    design.chips.main.size.size_y = f"{DIE}mm"
    return design


def stage_launchpads(design):
    """48 wire-bond launchpads, 12 per edge at 1 mm pitch (6 unused on the die)."""
    feed_seen = set()
    for p in DATA["launchpads"]:
        edge = EDGE_LETTER[p["edge"]]
        if p["edge"] in ("top", "bot"):
            x, y, slot = p["x"], math.copysign(RING, p["y"]), p["x"]
        else:
            x, y, slot = math.copysign(RING, p["x"]), p["y"], p["y"]
        if p["kind"] == "feed":
            grp = next(
                g
                for g, v in GROUPS.items()
                if any(
                    abs(px - p["x"]) < 0.01 and abs(py - p["y"]) < 0.01
                    for _, px, py in v["ports"]
                )
            )
            name = f"LP_feed_{grp}_{edge}"
            name += "b" if name in feed_seen else ""
            feed_seen.add(name)
        elif p["kind"] == "spare":
            name = f"LP_spare_{edge}_{slot_tag(slot)}"
        elif p["kind"] == "flux":
            name = f"LP_flux_{FLUX_QUBIT[f'{edge}{slot:+.1f}']}"
        else:
            name = f"LP_drive_{DRIVE_QUBIT[f'{edge}{slot:+.1f}']}"
        LaunchpadWirebond(
            design,
            name,
            options=dict(
                pos_x=f"{x}mm",
                pos_y=f"{y}mm",
                orientation=INWARD[p["edge"]],
                trace_width=CPW["width"],
                trace_gap=CPW["gap"],
                **PAD,
            ),
        )


def stage_qubits(design):
    """17 star transmons laid out like the device qubit (see ``pad_angles``).

    Five pads about 72 degrees apart and the junction on the island arm
    facing the flux line. Qubits on the edge of the lattice keep the pads
    without a neighbor, unconnected, as on the device.
    """
    for name, (col, row) in QUBITS.items():
        pads = pad_angles(name)
        StarQubit(
            design,
            name,
            options=dict(
                pos_x=f"{col * AX}mm",
                pos_y=f"{row * AY}mm",
                rotation_cpl1=arm_rotation(pads["cpl"][0]),
                rotation_cpl2=arm_rotation(pads["cpl"][90]),
                rotation_cpl3=arm_rotation(pads["cpl"][180]),
                rotation_cpl4=arm_rotation(pads["cpl"][270]),
                rotation_rdout=arm_rotation(pads["rdout"]),
                rotation_jj=arm_rotation(pads["jj"]),
                **STAR,
            ),
        )


def stage_couplers(design):
    """24 lattice couplers, one per nearest-neighbor pair."""
    for a, b, arm in bonds():
        key = f"{a}_{b}"
        pin_a, pin_b = ARM_PIN[arm], ARM_PIN[(arm + 4) % 8]
        mid = [np.array(p) for p in LINES["coupling"][key]]
        mid = [
            p
            for p in mid
            if np.linalg.norm(p - QUBIT_POS[a]) > PIN_R
            and np.linalg.norm(p - QUBIT_POS[b]) > PIN_R
        ]
        pa, pb = design.components[a].pins[pin_a], design.components[b].pins[pin_b]
        pts = join_pin(
            join_pin(mid, pa["middle"], pa["normal"], at="start"),
            pb["middle"],
            pb["normal"],
            at="end",
        )
        segs = draw_traced(design, f"CPL_{key}", pts, over=(), tag="ABC")
        design.connect_pins(
            design.components[a].id, pin_a, design.components[segs[0]].id, "start"
        )
        design.connect_pins(
            design.components[b].id, pin_b, design.components[segs[-1]].id, "end"
        )


def stage_control_lines(design):
    """17 flux lines (shorted beside the SQUID) and 17 drive lines (open).

    The flux line couples inductively and ends in a short; the drive line
    couples capacitively and must end open. Both cross earlier lines on
    airbridges.
    """
    for q, path in sorted(LINES["flux"]["path"].items()):
        lp = design.components[f"LP_flux_{q}"]
        pts = join_pad([np.array(p) for p in path], lp, at="start")
        pts = trim_to_standoff(pts, QUBIT_POS[q], FLUX_STANDOFF)
        segs = draw_traced(design, f"FLUX_{q}", pts, over=("CPL_",), tag="AB")
        terminate(design, f"FLUXSHORT_{q}", ShortToGround, pts, segs[-1], at="end")
        design.connect_pins(lp.id, "tie", design.components[segs[0]].id, "start")
    for q, path in sorted(LINES["drive"]["path"].items()):
        lp = design.components[f"LP_drive_{q}"]
        pts = join_pad([np.array(p) for p in path], lp, at="start")
        pts = trim_to_standoff(pts, QUBIT_POS[q], DRIVE_STANDOFF)
        segs = draw_traced(design, f"DRIVE_{q}", pts, over=("CPL_", "FLUX_"), tag="ABD")
        terminate(design, f"DRIVEOPEN_{q}", OpenToGround, pts, segs[-1], at="end")
        design.connect_pins(lp.id, "tie", design.components[segs[0]].id, "start")


def place_purcell_coupler(design, q, tip):
    """The finger-in-frame coupler at Purcell filter ``q``'s open end.

    Its near long side sits FEED_TO_FRAME from the feedline center, on the
    feed normal through the filter's end; its length is set per qubit.
    """
    feed = np.array(LINES["feed"][GROUP[q]])
    foot, _, _ = project(feed, tip)
    n = (tip - foot) / np.linalg.norm(tip - foot)
    center = foot + n * (FEED_TO_FRAME + CELL_W / 2)
    x, y, outer = min(
        CAPS["purcell_couplers"]["outer_length_um_at_mm"],
        key=lambda r: np.hypot(r[0] - center[0], r[1] - center[1]),
    )
    return CapFingerInFrame(
        design,
        f"PUCAP_{q}",
        options=dict(
            pos_x=f"{center[0]}mm",
            pos_y=f"{center[1]}mm",
            orientation=f"{math.degrees(math.atan2(-n[1], -n[0]))}",
            frame_length=f"{outer - _G * 1000}um",
            frame_width=f"{CELL_W * 1000}um",
            frame_trace=f"{CELL_TRACE * 1000}um",
            cap_gap=f"{_G * 1000}um",
            ground_gap=f"{_G * 1000}um",
            frame_cpw_width=CPW["width"],
            finger_cpw_width=CPW["width"],
        ),
    )


def stage_readout(design):
    """Readout resonators, Purcell filters and the capacitors between them.

    Both lines are quarter-wave (Heinsoo et al., PR Applied 10, 034040 (2018)):
    the readout resonator is open at the qubit and shorted at its far end; the
    Purcell filter is shorted at one end and open at a finger-in-frame coupler
    beside the feedline. A pair of pads midway between the two lines couples
    them (CapNInterdigital with two zero-length fingers).
    """
    rp = DATA["readout_purcell_coupler"]
    for q, path in sorted(LINES["readout"].items()):
        pin = np.array(design.components[q].pins["pin_rdout"]["middle"])
        normal = np.array(design.components[q].pins["pin_rdout"]["normal"])
        pts = [np.array(p) for p in path]
        if np.linalg.norm(pts[0] - QUBIT_POS[q]) > np.linalg.norm(
            pts[-1] - QUBIT_POS[q]
        ):
            pts = pts[::-1]
        pts = [p for p in pts if np.linalg.norm(p - QUBIT_POS[q]) > PIN_R]
        while len(pts) > 2 and (pts[0] - pin) @ normal < TRACE_STEP / 2:
            pts.pop(0)
        pts = [pin] + pts
        segs = draw_traced(
            design,
            f"RO_{q}",
            pts,
            over=("CPL_", "FLUX_", "DRIVE_"),
            tag="ABR",
            taps={"rp": rp[q]["center"]},
        )
        design.connect_pins(
            design.components[q].id, "pin_rdout", design.components[segs[0]].id, "start"
        )
        terminate(design, f"ROSHORT_{q}", ShortToGround, pts, segs[-1], at="end")

    for q, path in sorted(LINES["purcell"].items()):
        pts = [np.array(p) for p in path]  # shorted end -> open end
        cap = place_purcell_coupler(design, q, pts[-1])
        pts = join_pin(
            pts, cap.pins["frame"]["middle"], cap.pins["frame"]["normal"], at="end"
        )
        segs = draw_traced(
            design,
            f"PURCELL_{q}",
            pts,
            over=("CPL_", "FLUX_", "DRIVE_", "RO_"),
            tag="ABP",
            taps={"rp": rp[q]["center"]},
        )
        terminate(design, f"PUSHORT_{q}", ShortToGround, pts, segs[0], at="start")
        design.connect_pins(design.components[segs[-1]].id, "end", cap.id, "frame")

    for q in sorted(rp):
        ro = design.components[owner_of_pin(design, f"RO_{q}", "rp")]
        pu = design.components[owner_of_pin(design, f"PURCELL_{q}", "rp")]
        a, b = np.array(ro.pins["rp"]["middle"]), np.array(pu.pins["rp"]["middle"])
        span = np.linalg.norm(b - a)
        d = (b - a) / span
        stub = (span - RP["cap_gap_um"] / 1000 - 2 * RP["pad_width_um"] / 1000) / 2
        cap = CapNInterdigital(
            design,
            f"RPCAP_{q}",
            options=dict(
                pos_x=f"{a[0]}mm",
                pos_y=f"{a[1]}mm",
                orientation=f"{math.degrees(math.atan2(d[0], -d[1]))}",
                finger_count="2",
                finger_length="0um",
                cap_width=f"{RP['pad_width_um']}um",
                cap_gap=f"{RP['cap_gap_um']}um",
                cap_gap_ground=f"{RP['ground_gap_um']}um",
                cap_distance=f"{stub * 1000}um",
                north_width=CPW["width"],
                north_gap=CPW["gap"],
                south_width=CPW["width"],
                south_gap=CPW["gap"],
            ),
        )
        design.connect_pins(ro.id, "rp", cap.id, "north_end")
        design.connect_pins(cap.id, "south_end", pu.id, "rp")


def stage_feedlines(design):
    """4 readout feedlines, each with a series input capacitor and a stub to
    every Purcell coupler of its group.

    One through-line per group of 4-5 qubits (Krinner et al., Methods), from a
    launchpad on one edge to one on the adjacent edge. The input capacitor sits
    next to one launchpad, frame side toward it; which port is the input is not
    stated.
    """
    for grp, path in sorted(LINES["feed"].items()):
        ports = GROUPS[grp]["ports"]
        pads = [
            design.components[f"LP_feed_{grp}_{EDGE_LETTER[e]}"] for e, _, _ in ports
        ]
        pts = [np.array(p) for p in path]
        if np.linalg.norm(pts[0] - np.array(ports[0][1:])) > np.linalg.norm(
            pts[-1] - np.array(ports[0][1:])
        ):
            pts = pts[::-1]

        line = np.array(pts)
        s_all = np.concatenate(
            [[0], np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
        )
        center, s_c, tang = project(
            line, np.array(CAPS["input_caps"]["centers_mm"][grp])
        )
        near_start = s_c < s_all[-1] / 2
        u = tang if near_start else -tang
        ic = CapFingerInFrame(
            design,
            f"FEEDCAP_{grp}",
            options=dict(
                pos_x=f"{center[0]}mm",
                pos_y=f"{center[1]}mm",
                orientation=f"{math.degrees(math.atan2(u[1], u[0]))}",
                frame_length=f"{INPUT_CAP_L * 1000}um",
                frame_width=f"{CELL_W * 1000}um",
                frame_trace=f"{CELL_TRACE * 1000}um",
                cap_gap=f"{_G * 1000}um",
                ground_gap=f"{_G * 1000}um",
                frame_cpw_width=CPW["width"],
                finger_cpw_width=CPW["width"],
            ),
        )
        pin_h, pin_t = ("frame", "finger") if near_start else ("finger", "frame")
        head = [p for p, s in zip(pts, s_all) if s < s_c]
        tail = [p for p, s in zip(pts, s_all) if s > s_c]
        head = join_pin(
            join_pad(head, pads[0], at="start"),
            ic.pins[pin_h]["middle"],
            ic.pins[pin_h]["normal"],
            at="end",
        )
        tail = join_pad(
            join_pin(
                tail, ic.pins[pin_t]["middle"], ic.pins[pin_t]["normal"], at="start"
            ),
            pads[1],
            at="end",
        )

        caps = {q: design.components[f"PUCAP_{q}"] for q in GROUPS[grp]["qubits"]}
        taps_h, taps_t = {}, {}
        for q, c in caps.items():
            tgt = np.array(c.pins["finger"]["middle"])
            nearer_head = dist_to_polyline(tgt, np.array(head)) < dist_to_polyline(
                tgt, np.array(tail)
            )
            (taps_h if nearer_head else taps_t)[f"pu_{q}"] = tgt
        over = ("CPL_", "FLUX_", "DRIVE_", "RO_", "PURCELL_")
        name_h, name_t = (
            (f"FEEDIN_{grp}", f"FEED_{grp}")
            if near_start
            else (f"FEED_{grp}", f"FEEDIN_{grp}")
        )
        segs_h = draw_traced(design, name_h, head, over=over, tag="ABF", taps=taps_h)
        segs_t = draw_traced(design, name_t, tail, over=over, tag="ABF", taps=taps_t)
        design.connect_pins(pads[0].id, "tie", design.components[segs_h[0]].id, "start")
        design.connect_pins(design.components[segs_h[-1]].id, "end", ic.id, pin_h)
        design.connect_pins(ic.id, pin_t, design.components[segs_t[0]].id, "start")
        design.connect_pins(pads[1].id, "tie", design.components[segs_t[-1]].id, "end")

        for q, c in caps.items():
            host = design.components[
                owner_of_pin(design, f"FEED_{grp}", f"pu_{q}")
                or owner_of_pin(design, f"FEEDIN_{grp}", f"pu_{q}")
            ]
            stub = PolylineCPW(
                design,
                f"PUSTUB_{q}",
                options=dict(
                    points=[
                        list(map(float, host.pins[f"pu_{q}"]["middle"])),
                        list(map(float, c.pins["finger"]["middle"])),
                    ],
                    trace_width=CPW["width"],
                    trace_gap=CPW["gap"],
                ),
            )
            design.connect_pins(host.id, f"pu_{q}", stub.id, "start")
            design.connect_pins(stub.id, "end", c.id, "finger")


STAGES = [
    ("Die and launchpads", stage_launchpads),
    ("Qubits", stage_qubits),
    ("Lattice couplers", stage_couplers),
    ("Flux and drive lines", stage_control_lines),
    ("Readout resonators, Purcell filters and their couplers", stage_readout),
    ("Feedlines and input capacitors", stage_feedlines),
]


def build():
    """The complete chip."""
    design = new_design()
    for _, stage in STAGES:
        stage(design)
    return design


def pin_directions(design):
    """{qubit: {pin or "jj": compass angle}} read back from the BUILT qubits.

    Reads the drawn geometry rather than the options passed in -- the check
    that catches a rotation convention being off. Compare with
    :func:`pad_angles`.
    """
    tbl = design.qgeometry.tables["junction"]
    out = {}
    for q in QUBITS:
        comp = design.components[q]
        angles = {}
        for pin in ("pin_cpl1", "pin_cpl2", "pin_cpl3", "pin_cpl4", "pin_rdout"):
            n = comp.pins[pin]["normal"]
            angles[pin] = round(math.degrees(math.atan2(n[1], n[0]))) % 360
        jj = tbl[tbl.component == comp.id].geometry.iloc[0].centroid
        c = QUBIT_POS[q]
        angles["jj"] = round(math.degrees(math.atan2(jj.y - c[1], jj.x - c[0]))) % 360
        out[q] = angles
    return out


def expected_pin_directions(q):
    """What :func:`pin_directions` should read for qubit ``q``."""
    pads = pad_angles(q)
    exp = {
        f"pin_cpl{i}": pads["cpl"][arm] for i, arm in enumerate((0, 90, 180, 270), 1)
    }
    exp["pin_rdout"] = pads["rdout"]
    exp["jj"] = pads["jj"]
    return exp
