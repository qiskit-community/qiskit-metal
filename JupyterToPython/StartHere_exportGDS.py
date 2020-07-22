# To add a new cell, type '  '
# To add a new markdown cell, type ' '

#from IPython import get_ipython


# For convenience, let's begin by enabling [automatic reloading of modules](https://ipython.readthedocs.io/en/stable/config/extensions/autoreload.html?highlight=autoreload) when they change.


#get_ipython().run_line_magic('load_ext', 'autoreload')
#get_ipython().run_line_magic('autoreload', '2')


# # Import Qiskit Metal


from qiskit_metal.components.basic.rectangle_hollow import RectangleHollow
from qiskit_metal.components.basic.circle_raster import CircleRaster
from qiskit_metal.components.basic.n_gon import NGon
from qiskit_metal.components.interconnects.cpw_basic_straight_line import CpwStraightLine
from qiskit_metal.components.basic.n_square_spiral import NSquareSpiral
from qiskit_metal.components.interconnects.cpw_meander_simple import CpwMeanderSimple
from qiskit_metal.components.qubits.transmon_pocket import TransmonPocket
import qiskit_metal as metal
from qiskit_metal import designs, draw
from qiskit_metal import MetalGUI, Dict, Headings
from qiskit_metal.renderers.renderer_gds.gds_renderer import GDSRender


Headings.h1('Welcome to Qiskit Metal')


# Create a quantum design (`QDesign` class) and launch the gui (`MetalGUI`).<br>
# We can look at the library of `designs` to select a planar design (class `DesignPlanar`).


design = designs.DesignPlanar()
gui = MetalGUI(design)

# Now, we have a blank, empty quantum design, and the gui.


# Headings.h1('Hello Quantum World!')


# ### How do I know what the default options are?
#
# A QComponent is created with default options.
# To find out what these are use `QComponentClass.get_template_options(design)`
TransmonPocket.get_template_options(design)

# ### How do I change the default options?
# Now lets change the default options we will use to create the transmon

design.delete_all_components()

# Custom options for all the transmons
options = dict(
    # Some options we want to modify from the deafults
    # (see below for defaults)
    pad_width='425 um',
    pocket_height='650um',
    # Adding 4 connectors (see below for defaults)
    connection_pads=dict(
        a=dict(loc_W=+1, loc_H=+1),
        b=dict(loc_W=-1, loc_H=+1, pad_height='30um'),
        c=dict(loc_W=+1, loc_H=-1, pad_width='200um'),
        d=dict(loc_W=-1, loc_H=-1, pad_height='50um')
    )
)

# Create 4 transmons

q1 = TransmonPocket(design, 'Q1', options=dict(
    pos_x='+2.55mm', pos_y='+0.0mm', **options))
q2 = TransmonPocket(design, 'Q2', options=dict(
    pos_x='+0.0mm', pos_y='-0.9mm', orientation='90', **options))
q3 = TransmonPocket(design, 'Q3', options=dict(
    pos_x='-2.55mm', pos_y='+0.0mm', **options))
q4 = TransmonPocket(design, 'Q4', options=dict(
    pos_x='+0.0mm', pos_y='+0.9mm', orientation='90', **options))

# # Rebuild the design
# gui.rebuild()
# gui.autoscale()


# Let's import the basic cpw QComponent from the QLibrary. It is a class called `CpwMeanderSimple`.
# We can see its default options using `CpwMeanderSimple.get_template_options(design)`
CpwMeanderSimple.get_template_options(design)


# We can now modify the options and connect all four qubits.
# Since this is repetative, you can define a function to wrap up the repetatvie steps.
# Here we will call this `connect`. This function creates a `CpwMeanderSimple` QComponent class.
options = Dict(
    meander=Dict(
        lead_start='0.1mm',
        lead_end='0.1mm',
        asymmetry='0 um')
)


def connect(component_name: str, component1: str, pin1: str, component2: str, pin2: str,
            length: str,
            asymmetry='0 um', flip=False):
    """Connect two pins with a CPW."""
    myoptions = Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component=component1,
                pin=pin1),
            end_pin=Dict(
                component=component2,
                pin=pin2)),
        total_length=length)
    myoptions.update(options)
    myoptions.meander.asymmetry = asymmetry
    myoptions.meander.lead_direction_inverted = 'true' if flip else 'false'
    return CpwMeanderSimple(design, component_name, myoptions)


asym = 90
cpw1 = connect('cpw1', 'Q1', 'd', 'Q2', 'c', '6.0 mm', f'+{asym}um')
cpw2 = connect('cpw2', 'Q3', 'c', 'Q2', 'a', '6.1 mm', f'+{asym}um', flip=True)
cpw3 = connect('cpw3', 'Q3', 'a', 'Q4', 'b', '6.0 mm', f'+{asym}um')
cpw4 = connect('cpw4', 'Q1', 'b', 'Q4', 'd', '6.1 mm', f'+{asym}um', flip=True)

gui.rebuild()
gui.autoscale()
# gui.qApp.exec()

# print(design.components)
a_gds = GDSRender(design)

a_gds.path_and_poly_to_gds("../../GDS_files/StartHere.gds")

a_gds.path_and_poly_to_gds("../../GDS_files/four_qcomponents.gds",
                           highlight_qcomponents=['cpw1', 'cpw4', 'Q1', 'Q3'])


# We can access the created CPW from the desing too.


# print(design.components.cpw1)


# We can see all the pins


gui.highlight_components(
    ['Q1', 'Q2', 'Q3', 'Q4', 'cpw1', 'cpw2', 'cpw3', 'cpw4'])


Headings.h1('Variables in options')


# ## Varaibles

# The design can have variables, which can be used in the componetn options.


design.variables.cpw_width = '10um'
design.variables.cpw_gap = '6um'


# For example, we can all qubit pads using the variables.


# Set variables in the design
design.variables.pad_width = '550 um'

# Assign variables to component options
q1.options.pad_width = 'pad_width'
q2.options.pad_width = 'pad_width'
q3.options.pad_width = 'pad_width'

# Rebuild all compoinent and refresh the gui
gui.rebuild()
gui.autoscale()
# gui.screenshot()


Headings.h1('More QComponents')


# print(NSquareSpiral.get_template_options(design))
ops = {
    'n': '10',
    'width': '10um',
    'radius': '100um',
    'gap': '22um',
    'pos_x': '0.65mm',
    'pos_y': '2.2mm',
    'rotation': '0',
    'subtract': 'False'}
NSquareSpiral(design, 'spiral', ops)
NSquareSpiral(design, 'spiral_cut', {
              **ops, **dict(subtract=True, width='22um', gap='10um')})
gui.rebuild()


# CpwStraightLine.get_template_options(design)
myoptions = Dict(
    pin_inputs=Dict(
        start_pin=Dict(
            component='Q4',
            pin='c'),
        end_pin=Dict(
            component='spiral',
            pin='spiralPin'))
)


CpwStraightLine(design, 'cpw_s1', myoptions)
gui.rebuild()


qcomponents = ['spiral', 'cpw_s1']
gui.highlight_components(qcomponents)
# gui.zoom_on_components(qcomponents)
# gui.screenshot()


# ####  NGon


# print(NGon.get_template_options(design))
ops = {
    'n': '5',
    'radius': '250um',
    'pos_x': '-0.85mm',
    'pos_y': '2.0mm',
    'rotation': '15',
    'subtract': 'False',
    'helper': 'False',
    'chip': 'main',
    'layer': '1'}
NGon(design, 'ngon', ops)
NGon(design, 'ngon_negative', {**ops, **dict(subtract=True, radius='350um')})
gui.rebuild()


gui.zoom_on_components(['ngon_negative'])
# gui.screenshot()


print(CircleRaster.get_template_options(design))

ops = {'radius': '300um',
       'pos_x': '-1.5mm',
       'pos_y': '2mm',
       'resolution': '16',
       'cap_style': 'round',
       'subtract': 'False',
       'helper': 'False',
       'chip': 'main',
       'layer': '1'}
CircleRaster(design, 'CircleRaster', ops)
gui.rebuild()


gui.zoom_on_components(['CircleRaster'])
# gui.screenshot()


print(RectangleHollow.get_template_options(design))

ops = {'width': '500um',
       'height': '300um',
       'pos_x': '-2.3mm',
       'pos_y': '2mm',
       'rotation': '0',
       'subtract': 'False',
       'helper': 'False',
       'chip': 'main',
       'layer': '1',
       'inner': {'width': '250um',
                 'height': '100um',
                 'offset_x': '40um',
                 'offset_y': '-20um',
                 'rotation': '15'}}
RectangleHollow(design, 'RectangleHollow', ops)
gui.rebuild()


gui.zoom_on_components(['RectangleHollow'])
# gui.screenshot()


gui.autoscale()
# gui.screenshot()


Headings.h1('The geometry of QComponent: QGeometry')


# ### Geometric boundary of a qcomponent?
# Return the boundry box of the geometry, for example: `q1.qgeometry_bounds()`.
# The function returns a tuple containing (minx, miny, maxx, maxy) bound values
# for the bounds of the component as a whole.


for name, qcomponent in design.components.items():
    print(f"{name:10s} : {qcomponent.qgeometry_bounds()}")


# ### What is QGeometry?

# We can get all the QGeometry of a QComponent. There are several kinds, such as `path` and `poly`. Let us look at all the polygons used to create qubit `q1`


q1.qgeometry_table('poly')


# Paths are lines. These can have a width.


q1.qgeometry_table('path')


# Expalin shapely.


Headings.h1('Appendix')


# <br><br><br>
#
#
# ## Notes on modifing source code on the fly

# Enable module reloading; see [IPython documentation](https://ipython.readthedocs.io/en/stable/config/extensions/autoreload.html?highlight=autoreload).
#
#
# ``autoreload`` reloads modules automatically before entering the execution of
# code typed at the IPython prompt.
#
# This makes for example the following workflow possible:
#
# ```python
#    In [1]: %load_ext autoreload
#    In [2]: %autoreload 2
#
#    In [3]: from foo import some_function
#    In [4]: some_function()
#    Out[4]: 42
#
#    In [5]: # open foo.py in an editor and change some_function to return 43
#    In [6]: some_function()
#    Out[6]: 43
# ```
#
# The module was reloaded without reloading it explicitly, and the object
# imported with ``from foo import ...`` was also updated.


Headings.h1('Qiskit Metal Version')


metal.about()
