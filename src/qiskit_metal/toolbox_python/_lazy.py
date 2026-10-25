# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Import a compiled optional-at-import-time package on first use."""

import importlib


class LazyModule:
    """Stands in for a module and imports it when an attribute is first read.

    Keeps ``import qiskit_metal`` free of heavy compiled packages (qutip,
    gdstk) that the lite install path does not need until a feature uses them.
    """

    def __init__(self, name: str):
        self.__dict__["_name"] = name
        self.__dict__["_module"] = None

    def _load(self):
        module = self.__dict__["_module"]
        if module is None:
            module = importlib.import_module(self.__dict__["_name"])
            self.__dict__["_module"] = module
        return module

    def __getattr__(self, attr):
        return getattr(self._load(), attr)

    def __repr__(self):
        return f"<LazyModule {self.__dict__['_name']!r}>"
