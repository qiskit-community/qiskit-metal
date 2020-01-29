
import gdspy
import shapely

import qiskit_metal as metal
from qiskit_metal import draw_utility as draw
from qiskit_metal import Dict

from ..base_objects.Metal_Object import Metal_Object

from IPython.display import display

class MyGDSComponent(Metal_Object):

    def __init__(self, design, name, filename, scale=1, rotate_angle=90,
                 translate=[0, 0],
                 scale_origin=[0, 0, 0], rotate_origin=[0, 0, 0]):
        super().__init__(design, name=name, overwrite=True)

        self.filename = filename

        self.scale = scale
        self.scale_origin = scale_origin

        self.rotate_angle = rotate_angle
        self.rotate_origin = rotate_origin

        self.translate = translate

        self.lib = None
        self.polys = None

        self.read_in_gds()
        self.gds_to_elements()

    def read_in_gds(self):
        """Just do the quick and dirty import here for now.
        """

        # clear any existing cells; this is a bug i think
        gdspy.current_library.cells = dict()

        # The GDSII file is called a library, which contains multiple cells.
        lib = gdspy.GdsLibrary()
        lib.read_gds(self.filename)

        self.lib = lib

        print('Cells:')
        display(list(lib.cells.keys()))

        print('\nTop level cells:')
        lib.top_level()

    def gds_to_elements(self):

        # Get polygons
        cell = self.lib.top_level()[0]
        self.polys = cell.get_polygons()

        # Convert to internal rep elements
        objects = {str(x): shapely.geometry.Polygon(y) for x, y in enumerate(self.polys)}
        objects = draw.scale_objs(objects, xfact=self.scale,
                                  yfact=self.scale, origin=self.scale_origin)
        objects = draw.rotate_objs(objects, self.rotate_angle, origin=self.rotate_origin)
        objects = draw.translate_objs(objects, *self.translate)

        self.objects = objects

    def make(self):
        pass
