# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Suite-wide test configuration.

Quiet GUI mode for local runs: the on-screen GUI tests (and their
subprocess children, which inherit this environment) spawn real windows.
With ``QISKIT_METAL_GUI_NO_ACTIVATE`` set, Qt's ``AA_PluginApplication``
keeps the process from becoming the active application on macOS, so a
developer's editor keeps keyboard focus while the suite runs -- the
windows still create, paint, and receive QTest-injected events normally
(synthetic events target widgets directly and don't require OS-level
activation).

Deliberately NOT applied on CI (GitHub Actions always sets ``CI``):
the hosted runners have nobody to annoy, and they should keep exercising
the default activation path real users get -- the issue #1048 crash
class lives in exactly that on-screen init/paint machinery, so CI
narrowing to a quieter variant would weaken the coverage.

``setdefault`` so an explicit value (either way) always wins.
"""

import os

if not os.environ.get("CI"):
    os.environ.setdefault("QISKIT_METAL_GUI_NO_ACTIVATE", "1")


def pytest_collection_modifyitems(config, items):  # pylint: disable=unused-argument
    """Run in-process-Qt modules in child processes (see ``_gui_isolation``)."""
    from tests._gui_isolation import isolate_modules

    isolate_modules(items)
