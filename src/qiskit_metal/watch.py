# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Re-run a design script when it is saved, and refresh a picture and the checks.

    python -m qiskit_metal.watch my_design.py

Each time ``my_design.py`` changes, it is run, the variable ``design`` is
rendered to ``watch_out/design.png`` (open that file in an image viewer that
reloads, or in your editor's preview) and checked with
:func:`qiskit_metal.validation.validate`, and the report is printed. With
``--gds`` the design is also exported to ``watch_out/design.gds``, which KLayout
can reload. An error in the script is printed and the watch continues, so a typo
does not end the session.

The script is any Python file that leaves a ``QDesign`` in a variable named
``design`` (or the name given with ``--var``). Nothing here needs Qt.
"""

from __future__ import annotations

import argparse
import os
import runpy
import time
import traceback
from pathlib import Path

__all__ = ["main", "run_once", "watch"]


def run_once(script, out_dir="watch_out", var="design", gds=False, strict=False):
    """Run ``script`` once; render, check and (optionally) export its design.

    Args:
        script (str or Path): Python file that defines the design.
        out_dir (str or Path): where ``design.png`` (and ``design.gds``) go.
        var (str): name of the design variable the script leaves behind.
        gds (bool): also export ``design.gds``.
        strict (bool): count a finding of ERROR severity as a failed run.

    Returns:
        dict: ``ok`` (bool), ``report`` (str), ``files`` (list of Path) and, on a
        script error, ``error`` (str).
    """
    import matplotlib

    matplotlib.use("Agg", force=False)  # no window: this is a file-based loop

    from qiskit_metal import view
    from qiskit_metal.validation import validate

    script = Path(script)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    try:
        namespace = runpy.run_path(str(script), run_name="__watched__")
    except BaseException:  # a typo in the script must not end the watch
        return {"ok": False, "report": "", "files": [], "error": traceback.format_exc()}

    design = namespace.get(var)
    if design is None or not hasattr(design, "qgeometry"):
        return {
            "ok": False,
            "report": "",
            "files": [],
            "error": f"{script.name} did not leave a QDesign in a variable named '{var}'.",
        }

    files = []
    result = validate(design)
    fig = view(design)
    png = out / "design.png"
    fig.savefig(png, dpi=150)
    files.append(png)
    if gds:
        path = out / "design.gds"
        design.renderers.gds.export_to_gds(str(path))
        files.append(path)
    ok = result.ok if strict else True
    return {"ok": ok, "report": result.report(), "files": files}


def watch(script, interval=0.5, max_runs=None, **kwargs):
    """Run ``script`` now and again whenever its modification time changes."""
    script = Path(script)
    last = None
    runs = 0
    while max_runs is None or runs < max_runs:
        mtime = script.stat().st_mtime if script.exists() else None
        if mtime != last and mtime is not None:
            last = mtime
            runs += 1
            started = time.time()
            res = run_once(script, **kwargs)
            stamp = time.strftime("%H:%M:%S")
            if "error" in res:
                print(f"[{stamp}] {script.name}: error\n{res['error']}")
            else:
                print(f"[{stamp}] {script.name}: ran in {time.time() - started:.1f} s")
                print(res["report"])
                for f in res["files"]:
                    print(f"  wrote {f}")
        time.sleep(interval)
    return runs


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m qiskit_metal.watch", description=__doc__.split("\n\n")[0]
    )
    parser.add_argument("script", help="Python file that defines the design")
    parser.add_argument("--out", default="watch_out", help="output folder")
    parser.add_argument("--var", default="design", help="name of the design variable")
    parser.add_argument("--gds", action="store_true", help="also export design.gds")
    parser.add_argument("--interval", type=float, default=0.5, help="poll seconds")
    args = parser.parse_args(argv)
    if not os.path.exists(args.script):
        parser.error(f"{args.script} does not exist")
    print(f"Watching {args.script}; press Ctrl+C to stop.")
    try:
        watch(
            args.script,
            interval=args.interval,
            out_dir=args.out,
            var=args.var,
            gds=args.gds,
        )
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
