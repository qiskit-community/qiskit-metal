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

from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal import is_component
from qiskit_metal.qlibrary.core.base import QComponent
from qiskit_metal.qlibrary.core.qroute import QRoute, QRoutePoint, QRouteLead
from qiskit_metal.qlibrary.core.qubit import BaseQubit
