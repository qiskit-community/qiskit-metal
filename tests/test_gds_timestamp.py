# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""GDS export is byte-for-byte repeatable when SOURCE_DATE_EPOCH is set."""

import datetime
import os
import tempfile
import time
import unittest
from unittest import mock

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer


def _export(path):
    design = designs.DesignPlanar()
    TransmonPocket(design, "Q1")
    design.renderers.gds.export_to_gds(path)
    with open(path, "rb") as f:
        return f.read()


class TestGdsTimestamp(unittest.TestCase):
    def test_timestamp_is_none_without_the_variable(self):
        with mock.patch.dict(os.environ, clear=False):
            os.environ.pop("SOURCE_DATE_EPOCH", None)
            self.assertIsNone(QGDSRenderer._gds_timestamp())

    def test_timestamp_follows_source_date_epoch(self):
        with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
            self.assertEqual(
                QGDSRenderer._gds_timestamp(),
                datetime.datetime(2023, 11, 14, 22, 13, 20),
            )
        with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "not a number"}):
            self.assertIsNone(QGDSRenderer._gds_timestamp())

    def test_two_exports_are_identical_with_the_variable_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
                first = _export(os.path.join(tmp, "a.gds"))
                time.sleep(1.1)
                second = _export(os.path.join(tmp, "b.gds"))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
