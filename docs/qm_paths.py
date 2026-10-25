"""Learning paths: ordered notebooks that cross the part pages.

One source for two outputs, both built in ``conf.py``:

* the "Learning path" box that ``nbsphinx_prolog`` puts on each notebook page
  (step k of n, previous, next, link to the whole path);
* the body of ``choose-your-path.rst`` (replaces the ``{{ QM_PATHS }}`` token).

A notebook that is in no path gets no box. Paths only link notebooks; they do
not add toctree entries. Steps are ``(label, docname)`` with docnames relative
to ``docs/`` and without the ``.ipynb`` suffix.
"""

_T = "tut/"
_C = "circuit-examples/"
_AN = _T + "4-Analysis/"
_CP = _T + "2-From-components-to-chip/"
_RD = _T + "3-Renderers/"
_F = _C + "F.Small-quantum-chips/"

N = {
    "1.1": _T + "1-Overview/1.1-Quick-start",
    "1.2": _T + "1-Overview/1.2-Bird's-eye-view-of-Quantum-Metal",
    "1.3": _T + "1-Overview/1.3-Build-a-4-qubit-chip",
    "2.01": _CP + "2.01-How-to-use-a-QComponent",
    "2.11": _CP + "2.11-Routing-101",
    "2.12": _CP + "2.12-Simple-Meander",
    "2.21": _CP + "2.21-Design-a-4-qubit-full-chip",
    "2.24": _CP + "2.24-Design-rule-checking",
    "2.31": _CP + "2.31-Create-a-QComponent-Basic",
    "2.32": _CP + "2.32-Create-a-QComponent-Advanced",
    "2.33": _CP + "2.33-Add-my-QComponent-to-a-reusable-python-file",
    "3.1": _RD + "3.1-Introduction-to-QRenderers",
    "3.2": _RD + "3.2-Export-your-design-to-GDS",
    "3.3": _RD + "3.3-Render-your-design-to-Ansys",
    "3.4": _RD + "3.4-How-do-I-make-my-custom-QRenderer",
    "3.5": _RD + "3.5-Render-your-design-to-Gmsh",
    "4.01": _AN + "4.01-Capacitance-and-LOM",
    "4.02": _AN + "4.02-Eigenmode-and-EPR",
    "4.03": _AN + "4.03-Impedance",
    "4.04": _AN + "4.04-New-LOM-and-Fluxonium-Example",
    "4.11": _AN + "4.11-Analyze-and-tune-a-transmon",
    "4.13": _AN + "4.13-Analyze-transmon-and-resonator",
    "4.19": _AN + "4.19-Analyze-a-transmon-using-ElmerFEM",
    "4.31": _AN + "4.31-Plot-quantum-oscillator-wavefunction",
    "4.32": _AN + "4.32-Transmon-analytics-HCPB",
    "4.34": _AN + "4.34-Transmon-qubit-CPB-hamiltonian-charge-basis",
    "4.41": _AN + "4.41-The-package-mode-on-paper",
    "4.42": _AN + "4.42-Four-ways-to-measure-a-coupling",
    "4.43": _AN + "4.43-Mesh-and-solve-the-10x10-processor",
    "4.44": _AN + "4.44-Every-coupling-from-one-eigenmode",
    "4.45": _AN + "4.45-Four-methods-one-full-wave-model",
    "4.46": _AN + "4.46-Beyond-the-dipole-multipoles-and-magnetic-coupling",
    "A.1": _T + "full-design-examples/A.1-Transmon-with-readout-resonator",
    "A.2": _T + "full-design-examples/A.2-Two-coupled-transmons",
    "A.3": _T + "full-design-examples/A.3-Four-qubit-multiplexed-readout",
    "A.4": _C + "full-design-flow-examples/A.4-Full-chip-design",
    "F53": _F + "53-Wallraff_17Qubit_SurfaceCode",
    "F54": _F + "54-Wallraff_TwoQubit_Cell_Mesh",
}

# (key, title, description, [notebook ids])
PATHS = [
    (
        "chip-designer",
        "Chip designer",
        "Layout to GDS, no solver.",
        ["1.1", "1.3", "2.01", "2.11", "2.12", "2.21", "2.24", "3.2", "A.3", "F53"],
    ),
    (
        "open-source-simulation",
        "Open-source simulation",
        "Meshing and solving with gmsh, ElmerFEM and scikit-fem.",
        ["1.1", "3.5", "4.19", "4.41", "4.42", "4.43", "4.44", "4.45", "F54"],
    ),
    (
        "ansys-analyst",
        "Ansys EPR and LOM analyst",
        "Render to Ansys, then EPR and LOM analysis. Needs Ansys.",
        ["1.1", "3.3", "4.01", "4.02", "4.03", "4.11", "4.13", "4.04", "A.4"],
    ),
    (
        "teaching",
        "Teaching",
        "Runs in Colab: no solver, no GUI.",
        ["1.1", "1.2", "4.31", "4.32", "4.34", "4.41", "4.42", "A.1", "A.2"],
    ),
    (
        "component-developer",
        "Component developer",
        "Write a QComponent and a renderer.",
        ["2.01", "2.31", "2.32", "2.33", "3.1", "3.4"],
    ),
    (
        "package-modes-series",
        "Package modes and qubit couplings (series)",
        "Notebooks 4.41 to 4.46, in order.",
        ["4.41", "4.42", "4.43", "4.44", "4.45", "4.46"],
    ),
]


def _doc(nid):
    return N[nid]


def check(srcdir):
    """Raise ValueError when a path names a notebook that does not exist."""
    import os

    missing = [
        nid
        for _, _, _, ids in PATHS
        for nid in ids
        if nid not in N or not os.path.isfile(os.path.join(srcdir, N[nid] + ".ipynb"))
    ]
    if missing:
        raise ValueError(f"qm_paths: missing notebooks {sorted(set(missing))}")


def by_doc():
    """``{docname: [rst line, ...]}`` for the per-notebook box."""
    out = {}
    for key, title, _, ids in PATHS:
        n = len(ids)
        for k, nid in enumerate(ids):
            parts = [f"**{title}**: step {k + 1} of {n}"]
            if k > 0:
                prev = ids[k - 1]
                parts.append(f":doc:`← {prev} </{_doc(prev)}>`")
            if k < n - 1:
                nxt = ids[k + 1]
                parts.append(f":doc:`{nxt} → </{_doc(nxt)}>`")
            parts.append(f":ref:`all of this path <path-{key}>`")
            out.setdefault(_doc(nid), []).append(" · ".join(parts))
    return out


def page_body():
    """RST for ``choose-your-path.rst``: one section per path."""
    lines = []
    for key, title, desc, ids in PATHS:
        lines += [f".. _path-{key}:", "", title, "=" * len(title), "", desc, ""]
        for nid in ids:
            lines.append(f"#. :doc:`/{_doc(nid)}`")
        lines.append("")
    return "\n".join(lines)
