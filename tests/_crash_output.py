# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Readable stderr excerpts from crashed test subprocesses.

When a child process dies natively under ``-X faulthandler``, its stderr
ends with one very long ``Extension modules: ...`` line. A plain
``stderr[-2000:]`` tail then shows only that list and cuts off the
traceback that says where the crash happened (issue #1048).
"""

_CRASH_HEADERS = (
    "Fatal Python error",
    "Windows fatal exception",
)


def crash_excerpt(stderr: str, limit: int = 4000, context: int = 15) -> str:
    """Return the part of ``stderr`` that explains a crash.

    Drops faulthandler's ``Extension modules:`` line. If a faulthandler
    header is present, returns up to ``limit`` characters starting
    ``context`` lines before the first one (e.g. a Qt plugin error),
    through the fatal error and every thread's stack; otherwise returns
    the last ``limit`` characters.
    """
    if not stderr:
        return ""
    lines = [
        line
        for line in stderr.splitlines()
        if not line.lstrip().startswith("Extension modules:")
    ]
    starts = [i for i, line in enumerate(lines) if line.startswith(_CRASH_HEADERS)]
    if starts:
        excerpt = "\n".join(lines[max(0, starts[0] - context) :])
        if len(excerpt) > limit:
            excerpt = excerpt[:limit] + "\n[... truncated ...]"
        return excerpt
    return "\n".join(lines)[-limit:]
