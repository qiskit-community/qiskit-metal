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

"""Opt-in init-tracing for MetalGUI (issues #1048 / #1109).

Several reporters see ``MetalGUI.__init__`` silently abort mid-init on
Windows 11 with no Python traceback. ``QISKIT_METAL_DEBUG_INIT=1`` makes
each init step print to stderr with an explicit flush, so the last
printed line identifies the failing call without needing a custom
branch or screenshare.

Lives in its own module so both ``main_window`` and ``main_window_base``
can import it without a circular dependency. No Qt or metal imports
here -- just os + sys -- so this stays usable from anywhere.
"""

import os
import sys


def trace_init(step: str) -> None:
    """Print ``step`` to stderr when QISKIT_METAL_DEBUG_INIT is truthy.

    Truthy = any value other than the empty string, ``0``, ``false``,
    ``no``, or ``off`` (case-insensitive). Always flushes so a
    subsequent crash doesn't swallow the marker. No-op when unset.

    Args:
        step: Short label for the init step about to be executed. Free
            text. Use the function/method name that follows for clarity.
    """
    val = os.environ.get("QISKIT_METAL_DEBUG_INIT", "")
    if not val or val.lower() in ("0", "false", "no", "off"):
        return
    print(f"[metal-init] {step}", file=sys.stderr, flush=True)
