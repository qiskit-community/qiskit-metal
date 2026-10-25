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

import pytest

if not os.environ.get("CI"):
    os.environ.setdefault("QISKIT_METAL_GUI_NO_ACTIVATE", "1")


_GUI_OPT_IN_ENV = "QISKIT_METAL_RUN_CRASHY_GUI_TESTS"

# GUI modules that build a real MetalGUI in a child process and still hit the
# native crashes of issue #1048 (CI: macOS rc=-11, Windows access violation).
# Opt-in: pass --run-crashy-gui, or set the env var above to 1. Run them
# locally when ``_gui/`` is touched, and in the dedicated tests-gui-display jobs.
CRASHY_GUI_MODULES = frozenset(
    {
        "test_gui_nudge.py",
        "test_gui_init.py",
        "test_gui_left_dock_min_width.py",
    }
)


def pytest_addoption(parser):
    parser.addoption(
        "--run-crashy-gui",
        action="store_true",
        default=False,
        help=(
            "Also run the GUI modules that still crash intermittently "
            f"({', '.join(sorted(CRASHY_GUI_MODULES))}). "
            f"Same as {_GUI_OPT_IN_ENV}=1."
        ),
    )


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    """Skip the crash-prone GUI modules unless opted in; isolate the rest.

    In-process-Qt modules run in child processes (see ``_gui_isolation``).
    """
    from tests._gui_isolation import isolate_modules

    if config.getoption("--run-crashy-gui"):
        os.environ[_GUI_OPT_IN_ENV] = "1"  # child pytest processes inherit it
    if os.environ.get(_GUI_OPT_IN_ENV) != "1":
        skip = pytest.mark.skip(
            reason=(
                "crash-prone GUI test (#1048); opt in with --run-crashy-gui "
                f"or {_GUI_OPT_IN_ENV}=1"
            )
        )
        for item in items:
            if os.path.basename(str(item.fspath)) in CRASHY_GUI_MODULES:
                item.add_marker(skip)
    isolate_modules(items)
