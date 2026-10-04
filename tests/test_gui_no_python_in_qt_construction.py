# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Guard: no Python in Qt's construction path, no nested loops in refresh.

Two patterns were behind intermittent native startup segfaults on CI
(``rc=-11`` / Windows access violations, different Python frames each time,
empty stdout; see ``docs/architecture/gui_crash_defenses.md``, failure
mode 5):

* a Python ``childEvent`` override on a widget -- Qt calls it from inside
  C++ child construction and destruction;
* ``flush_events()`` / ``processEvents()`` inside ``MplCanvas.refresh()`` --
  a nested event loop on every refresh, including startup ones.

A crash from either is a use-after-free no traceback explains and a single
CI run cannot catch (~2% per start), so this is a static check.
"""

import ast
from pathlib import Path

import qiskit_metal

SRC = Path(qiskit_metal.__file__).parent


def test_no_childevent_override_in_gui():
    offenders = []
    for path in (SRC / "_gui").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "childEvent":
                offenders.append(f"{path.relative_to(SRC)}:{node.lineno}")
    assert not offenders, (
        "Python childEvent override runs inside Qt widget construction; "
        f"use a signal or showEvent sweep instead: {offenders}"
    )


def test_mpl_refresh_spins_no_event_loop():
    path = SRC / "renderers" / "renderer_mpl" / "mpl_canvas.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "refresh":
            calls = {
                n.func.attr
                for n in ast.walk(node)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            }
            assert not calls & {"flush_events", "processEvents"}, (
                "MplCanvas.refresh must not run a nested Qt event loop"
            )
