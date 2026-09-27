# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""QComponent.to_html / _repr_html_: options with their docs, and pins."""

import importlib
import inspect
import pkgutil
import unittest

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.core._html_repr import option_docs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander


class TestOptionDocs(unittest.TestCase):
    def test_nested_options(self):
        docs = option_docs(RouteMeander)
        self.assertIn("straight segment", docs[("lead", "start_straight")])
        self.assertIn("start from", docs[("pin_inputs", "start_pin", "component")])

    def test_slash_names_document_both(self):
        docs = option_docs(TransmonPocket)
        self.assertEqual(docs[("pos_x",)], docs[("pos_y",)])
        self.assertIn("position", docs[("pos_x",)])

    def test_empty_subclass_entry_keeps_parent_text(self):
        # BaseQubit lists pos_x without a description; QComponent has one.
        self.assertTrue(option_docs(TransmonPocket)[("pos_x",)])

    def test_wrapped_description_is_joined(self):
        docs = option_docs(TransmonPocket)
        self.assertIn("counter-clockwise", docs[("orientation",)])


class TestToHtml(unittest.TestCase):
    def setUp(self):
        self.design = designs.DesignPlanar()
        pads = dict(connection_pads=dict(a=dict(loc_W=1, loc_H=1)))
        self.q1 = TransmonPocket(self.design, "Q1", options=dict(pos_x="-1mm", **pads))
        self.q2 = TransmonPocket(
            self.design, "Q2", options=dict(pos_x="1mm", orientation="180", **pads)
        )
        self.route = RouteMeander(
            self.design,
            "R",
            options=Dict(
                total_length="5mm",
                pin_inputs=Dict(
                    start_pin=Dict(component="Q1", pin="a"),
                    end_pin=Dict(component="Q2", pin="a"),
                ),
            ),
        )

    def test_repr_html_is_to_html(self):
        self.assertEqual(self.q1._repr_html_(), self.q1.to_html())

    def test_options_and_docs(self):
        page = self.q1.to_html()
        self.assertIn("pad_gap", page)
        self.assertIn("distance between the two charge islands", page)
        # A pad under connection_pads uses the _default_connection_pads docs.
        self.assertIn("Width (x-axis) of the connector pad", page)

    def test_without_docs(self):
        page = self.q1.to_html(docs=False)
        self.assertNotIn("<th>description</th>", page)
        self.assertNotIn("distance between the two charge islands", page)

    def test_parsed_column_is_on_by_default(self):
        page = self.q1.to_html()
        self.assertIn("<th>parsed</th>", page)
        self.assertIn("-1", page)  # pos_x '-1mm' parsed to -1 (mm)
        self.assertNotIn("<th>parsed</th>", self.q1.to_html(parsed=False))

    def test_renderer_options_are_documented(self):
        """hfss_inductance etc. come from the renderers' element_table_docs."""
        from qiskit_metal.qlibrary.qubits.star_qubit import StarQubit

        star = StarQubit(self.design, "S")
        page = star.to_html()
        self.assertIn(
            "Junction inductance used when the junction is rendered to hfss", page
        )
        self.assertIn("Segments per quarter circle", page)  # StarQubit.resolution
        self.assertIn("cuts in the ground plane", page)  # common option: subtract

    def test_image_option(self):
        self.assertNotIn("data:image/png;base64", self.q1.to_html())
        self.assertIn("data:image/png;base64", self.q1.to_html(image=True))

    def test_pins_show_connections(self):
        page = self.q1.to_html()
        self.assertIn("connected to", page)
        self.assertIn("R.start", page)
        self.assertNotIn("connected to", self.q1.to_html(pins=False))

    def test_values_are_escaped(self):
        self.q1.options.chip = "<b>x</b>"
        page = self.q1.to_html()
        self.assertNotIn("<b>x</b>", page)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", page)


class TestDesignViews(unittest.TestCase):
    def setUp(self):
        self.design = designs.DesignPlanar()
        TransmonPocket(self.design, "Q1")

    def test_design_is_subscriptable(self):
        self.assertIs(self.design["Q1"], self.design.components["Q1"])
        self.assertIn("Q1", self.design)
        self.assertNotIn("nope", self.design)
        with self.assertRaises(KeyError):
            self.design["nope"]

    def test_design_html(self):
        page = self.design._repr_html_()
        self.assertIn("DesignPlanar", page)
        self.assertIn("TransmonPocket", page)
        self.assertIn("cpw_width", page)  # design variables

    def test_components_html(self):
        page = self.design.components._repr_html_()
        self.assertIn("Q1", page)
        self.assertIn("TransmonPocket", page)


class TestEveryComponentRenders(unittest.TestCase):
    """A repr must never raise: render every library component at defaults."""

    def test_all(self):
        from qiskit_metal import qlibrary
        from qiskit_metal.qlibrary.core import QComponent, QRoute

        seen = set()
        for info in pkgutil.walk_packages(qlibrary.__path__, "qiskit_metal.qlibrary."):
            if ".core" in info.name:
                continue
            module = importlib.import_module(info.name)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if (
                    cls.__module__ != module.__name__
                    or not issubclass(cls, QComponent)
                    or issubclass(cls, QRoute)
                    or inspect.isabstract(cls)
                    or cls in seen
                ):
                    continue
                seen.add(cls)
                with self.subTest(component=name):
                    component = cls(designs.DesignPlanar(), "c")
                    page = component.to_html(parsed=True)
                    self.assertIn('class="qm-comp"', page)
        self.assertGreater(len(seen), 20)


if __name__ == "__main__":
    unittest.main()
