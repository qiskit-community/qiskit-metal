# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Static AST audit: every ``self.options.<key>`` access in a
``QComponent.make()`` must be a key that exists in the merged
``default_options`` dict.

This catches the silent ``KeyError`` class of bug — a component
referencing an option name that doesn't exist in its (or its
ancestor's) ``default_options``. At instantiation time today, that
raises ``KeyError`` from a deep call stack; users typically blame
their own code.  Catching it at test time gives the maintainer a
clear signal at PR time instead.

How the audit works
-------------------

For each component class:

1. Parse the source file with :mod:`ast`.
2. Walk the class body for ``make()`` and any ``make_*`` helper.
3. Collect every static attribute / subscript access via the
   patterns ``self.options.<name>``, ``self.options['<name>']``,
   ``self.p.<name>``, ``self.p['<name>']``, and the same after the
   common local aliases ``p = self.p`` and ``o = self.options``.
4. Get the class's merged options via
   ``cls.get_template_options(DesignPlanar())`` — same call path used
   at runtime when the component is instantiated.
5. Assert every collected key is in the merged set.

Dynamic accesses (``self.p[name]`` where ``name`` is a variable) are
intentionally skipped — they're the right tool for, e.g., iterating
over ``connection_pads``. We only flag static accesses we can resolve.

Scope: every component in ``COMPONENTS_UNDER_TEST`` from the
idempotency suite (28 classes). Routes are excluded for the same
reason as in idempotency — their ``make()`` reads ``pin_inputs``
which aren't in default options.
"""

import ast
import inspect
import unittest
from typing import Set

from qiskit_metal import designs
from qiskit_metal.qlibrary.couplers.cap_n_interdigital_tee import CapNInterdigitalTee
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.couplers.line_tee import LineTee
from qiskit_metal.qlibrary.lumped.cap_3_interdigital import Cap3Interdigital
from qiskit_metal.qlibrary.lumped.cap_n_interdigital import CapNInterdigital
from qiskit_metal.qlibrary.lumped.resonator_coil_rect import ResonatorCoilRect
from qiskit_metal.qlibrary.qubits.JJ_Dolan import jj_dolan
from qiskit_metal.qlibrary.qubits.JJ_Manhattan import jj_manhattan
from qiskit_metal.qlibrary.qubits.SQUID_loop import SQUID_LOOP
from qiskit_metal.qlibrary.qubits.star_qubit import StarQubit
from qiskit_metal.qlibrary.qubits.transmon_concentric import TransmonConcentric
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_cross_fl import TransmonCrossFL
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.qlibrary.qubits.transmon_pocket_cl import TransmonPocketCL
from qiskit_metal.qlibrary.qubits.transmon_pocket_teeth import TransmonPocketTeeth
from qiskit_metal.qlibrary.sample_shapes.circle_caterpillar import CircleCaterpillar
from qiskit_metal.qlibrary.sample_shapes.circle_raster import CircleRaster
from qiskit_metal.qlibrary.sample_shapes.n_gon import NGon
from qiskit_metal.qlibrary.sample_shapes.n_square_spiral import NSquareSpiral
from qiskit_metal.qlibrary.sample_shapes.rectangle import Rectangle
from qiskit_metal.qlibrary.sample_shapes.rectangle_hollow import RectangleHollow
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.launchpad_wb_coupled import (
    LaunchpadWirebondCoupled,
)
from qiskit_metal.qlibrary.terminations.launchpad_wb_driven import (
    LaunchpadWirebondDriven,
)
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.terminations.short_to_ground import ShortToGround

COMPONENTS_UNDER_TEST = [
    Rectangle,
    RectangleHollow,
    NGon,
    NSquareSpiral,
    CircleRaster,
    CircleCaterpillar,
    OpenToGround,
    ShortToGround,
    LaunchpadWirebond,
    LaunchpadWirebondCoupled,
    LaunchpadWirebondDriven,
    TransmonConcentric,
    TransmonPocket,
    TransmonPocketCL,
    TransmonPocket6,
    TransmonPocketTeeth,
    TransmonCross,
    TransmonCrossFL,
    StarQubit,
    SQUID_LOOP,
    jj_dolan,
    jj_manhattan,
    CapNInterdigital,
    Cap3Interdigital,
    ResonatorCoilRect,
    LineTee,
    CapNInterdigitalTee,
    CoupledLineTee,
]


class _OptionsAccessCollector(ast.NodeVisitor):
    """AST visitor that collects keys accessed via ``self.options``,
    ``self.p``, and their common local aliases (``p = self.p``,
    ``o = self.options``).

    Only static accesses are recorded — i.e., ``self.p.foo`` or
    ``self.p['foo']`` where ``foo`` is a literal. Dynamic accesses
    like ``self.p[name]`` are intentionally skipped because the key
    is a runtime variable.
    """

    def __init__(self):
        self.keys: Set[str] = set()
        # Local variable aliases: name -> "options" | "p"
        self._aliases: dict[str, str] = {"self.options": "options", "self.p": "p"}

    # --- helpers ---------------------------------------------------

    @staticmethod
    def _expr_to_str(node: ast.AST) -> str:
        """Stringify a simple Attribute / Name chain like
        ``self.p`` or ``self.options`` — used to recognise aliases.
        Returns ``None`` for anything more complex."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = _OptionsAccessCollector._expr_to_str(node.value)
            if base is None:
                return None
            return f"{base}.{node.attr}"
        return None

    def _is_options_ref(self, node: ast.AST) -> bool:
        """Return True if ``node`` evaluates to ``self.options`` or
        ``self.p`` (directly or via a known local alias)."""
        s = self._expr_to_str(node)
        if s is None:
            return False
        if s in ("self.options", "self.p"):
            return True
        # Local alias: a single name like ``p`` or ``o``.
        if "." not in s and s in self._aliases:
            return True
        return False

    # --- AST handlers ---------------------------------------------

    def visit_Assign(self, node: ast.Assign):
        # Track aliases like ``p = self.p`` and ``o = self.options``.
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            value_str = self._expr_to_str(node.value)
            if value_str == "self.p":
                self._aliases[target_name] = "p"
            elif value_str == "self.options":
                self._aliases[target_name] = "options"
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # ``self.options.foo`` / ``self.p.foo`` / ``p.foo`` / ``o.foo``
        if self._is_options_ref(node.value) and isinstance(node.attr, str):
            # Skip dunder / private-ish attrs — these aren't option keys.
            if not node.attr.startswith("_"):
                self.keys.add(node.attr)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        # ``self.options['foo']`` / ``self.p['foo']`` / ``p['foo']``
        if self._is_options_ref(node.value):
            sub = node.slice
            # py3.9+ unwraps to the bare value; py3.8 wrapped in Index.
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                self.keys.add(sub.value)
            # Dynamic key (variable, expression) — skip silently.
        self.generic_visit(node)


def _collect_option_accesses(cls) -> Set[str]:
    """Return the set of option keys statically referenced anywhere
    in the class body (across all methods)."""
    src = inspect.getsource(cls)
    tree = ast.parse(src)
    collector = _OptionsAccessCollector()
    collector.visit(tree)
    return collector.keys


def _flatten_keys(d, parent_key: str = "") -> Set[str]:
    """Flatten a (potentially nested) options dict into a set of
    top-level keys. Only the top-level names are meaningful for the
    audit — nested keys are accessed via ``self.p.parent.child`` and
    ``parent`` is what shows up in default_options."""
    return set(d.keys()) if hasattr(d, "keys") else set()


class TestDefaultOptionsCompleteness(unittest.TestCase):
    """Every option key accessed in a component's ``make()`` (and
    helpers) must exist in the merged ``default_options``."""

    # Keys that look like option accesses to the AST visitor but are
    # actually method calls or addict.Dict convenience attributes. The
    # audit can't tell ``self.p.update(...)`` from ``self.p.some_key``
    # at parse time — both surface as ``.update`` / ``.some_key``
    # attribute accesses. Excluding these false-positives keeps the
    # signal real.
    FALSE_POSITIVE_NAMES = {
        # addict.Dict / dict methods
        "update",
        "get",
        "keys",
        "values",
        "items",
        "pop",
        "copy",
        "to_dict",
        "setdefault",
        "clear",
        "fromkeys",
        "popitem",
        # Common Python protocol methods
        "__init__",
        "__call__",
        "__getitem__",
        "__setitem__",
        # ParsedDynamicAttributes_Component internal API surface
        "_parent",
    }

    def test_make_only_references_existing_options(self):
        for cls in COMPONENTS_UNDER_TEST:
            with self.subTest(component=cls.__name__):
                design = designs.DesignPlanar()
                merged = cls.get_template_options(design)
                merged_keys = set(merged.keys())

                accessed = _collect_option_accesses(cls)
                accessed -= self.FALSE_POSITIVE_NAMES

                missing = accessed - merged_keys
                self.assertEqual(
                    missing,
                    set(),
                    f"{cls.__name__}.make() (or a helper) references "
                    f"option key(s) {sorted(missing)} that are not in "
                    f"the merged default_options "
                    f"(have: {sorted(merged_keys)}). "
                    f"This raises KeyError at runtime when the component "
                    f"is instantiated without explicit override.",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
