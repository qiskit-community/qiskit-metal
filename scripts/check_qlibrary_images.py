#!/usr/bin/env python3
"""CI gate: verify every ``.. image::`` directive in ``qlibrary/`` resolves.

Catches three failure modes:

  1. Broken refs — file doesn't exist (case-sensitive). macOS's HFS+/APFS
     is case-insensitive by default, so a docstring pointing at
     ``SQUID_LOOP.png`` silently resolves to ``squid_loop.png`` on the
     developer laptop but breaks the GUI on a Linux CI machine.

  2. One-line directives — ``.. image:: foo.png`` parses in Sphinx but is
     invisible to the ``MetalGUI`` scanner regex
     (``\\.\\. image::[\\r\\n]+([^\\r\\n]+)``); must be two lines.

  3. Orphan PNGs — a class has a matching ``<ClassName>.png`` on disk
     but no ``.. image::`` directive, so the GUI falls back to the
     generic placeholder.

Thin wrapper around ``_dev/generate_qlibrary_thumbnails.py --verify``.
Lives under ``scripts/`` to keep CI yaml clean and to mirror the
existing ``check_*.py`` gates.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    script = REPO / "_dev" / "generate_qlibrary_thumbnails.py"
    result = subprocess.run(
        [sys.executable, str(script), "--verify"],
        cwd=str(REPO),
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
