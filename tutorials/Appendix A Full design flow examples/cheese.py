from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder

from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond

from qiskit_metal.qlibrary.tlines.meandered import RouteMeander

from qiskit_metal.qlibrary.lumped.cap_3_interdigital import Cap3Interdigital

from qiskit_metal.qlibrary.qubits.transmon_pocket_cl import TransmonPocketCL

from qiskit_metal import designs, MetalGUI

design = designs.DesignPlanar()

gui = MetalGUI(design)

# WARNING
#options_connection_pads failed to have a value
Q1 = TransmonPocketCL(
    design,
    name='Q1',
    options={
        'cl_pocket_edge': '180',
        'connection_pads': {
            'bus': {
                'cpw_extend': '100um',
                'cpw_gap': 'cpw_gap',
                'cpw_width': 'cpw_width',
                'loc_H': -1,
                'loc_W': -1,
                'pad_cpw_extent': '25um',
                'pad_cpw_shift': '5um',
                'pad_gap': '15um',
                'pad_height': '30um',
                'pad_width': '125um',
                'pocket_extent': '5um',
                'pocket_rise': '65um'
            },
            'readout': {
                'cpw_extend': '100um',
                'cpw_gap': 'cpw_gap',
                'cpw_width': 'cpw_width',
                'loc_H': 1,
                'loc_W': 1,
                'pad_cpw_extent': '25um',
                'pad_cpw_shift': '5um',
                'pad_gap': '15um',
                'pad_height': '30um',
                'pad_width': '125um',
                'pocket_extent': '5um',
                'pocket_rise': '65um'
            }
        },
        'gds_cell_name': 'FakeJunction_01',
        'hfss_inductance': '14nH',
        'pad_width': '425 um',
        'pos_x': '0.7mm',
        'pos_y': '0mm'
    },
)

# WARNING
#options_connection_pads failed to have a value
Q2 = TransmonPocketCL(
    design,
    name='Q2',
    options={
        'cl_pocket_edge': '180',
        'connection_pads': {
            'bus': {
                'cpw_extend': '100um',
                'cpw_gap': 'cpw_gap',
                'cpw_width': 'cpw_width',
                'loc_H': -1,
                'loc_W': -1,
                'pad_cpw_extent': '25um',
                'pad_cpw_shift': '5um',
                'pad_gap': '15um',
                'pad_height': '30um',
                'pad_width': '125um',
                'pocket_extent': '5um',
                'pocket_rise': '65um'
            },
            'readout': {
                'cpw_extend': '100um',
                'cpw_gap': 'cpw_gap',
                'cpw_width': 'cpw_width',
                'loc_H': 1,
                'loc_W': 1,
                'pad_cpw_extent': '25um',
                'pad_cpw_shift': '5um',
                'pad_gap': '15um',
                'pad_height': '30um',
                'pad_width': '125um',
                'pocket_extent': '5um',
                'pocket_rise': '65um'
            }
        },
        'gds_cell_name': 'FakeJunction_02',
        'hfss_inductance': '12nH',
        'orientation': '180',
        'pad_width': '425 um',
        'pos_x': '-0.7mm',
        'pos_y': '0mm'
    },
)

Bus_Q1_Q2 = RoutePathfinder(
    design,
    name='Bus_Q1_Q2',
    options={
        '_actual_length': '0.8550176727053895 '
                          'mm',
        'fillet': '99um',
        'lead': {
            'end_jogged_extension': '',
            'end_straight': '250um',
            'start_jogged_extension': '',
            'start_straight': '0mm'
        },
        'pin_inputs': {
            'end_pin': {
                'component': 'Q2',
                'pin': 'bus'
            },
            'start_pin': {
                'component': 'Q1',
                'pin': 'bus'
            }
        },
        'trace_gap': 'cpw_gap'
    },
    type='CPW',
)

Cap_Q1 = Cap3Interdigital(
    design,
    name='Cap_Q1',
    options={
        'finger_length': '40um',
        'orientation': '90',
        'pos_x': '2.5mm',
        'pos_y': '0.25mm'
    },
    component_template=None,
)

Cap_Q2 = Cap3Interdigital(
    design,
    name='Cap_Q2',
    options={
        'finger_length': '40um',
        'orientation': '-90',
        'pos_x': '-2.5mm',
        'pos_y': '-0.25mm'
    },
    component_template=None,
)

Readout_Q1 = RouteMeander(
    design,
    name='Readout_Q1',
    options={
        '_actual_length': '5.000000000000001 '
                          'mm',
        'fillet': '99um',
        'lead': {
            'end_jogged_extension': '',
            'end_straight': '125um',
            'start_jogged_extension': '',
            'start_straight': '0.325mm'
        },
        'meander': {
            'asymmetry': '-50um',
            'spacing': '200um'
        },
        'pin_inputs': {
            'end_pin': {
                'component': 'Cap_Q1',
                'pin': 'a'
            },
            'start_pin': {
                'component': 'Q1',
                'pin': 'readout'
            }
        },
        'total_length': '5mm',
        'trace_gap': 'cpw_gap'
    },
    type='CPW',
)

Readout_Q2 = RouteMeander(
    design,
    name='Readout_Q2',
    options={
        '_actual_length': '5.999999999999999 '
                          'mm',
        'fillet': '99um',
        'lead': {
            'end_jogged_extension': '',
            'end_straight': '125um',
            'start_jogged_extension': '',
            'start_straight': '0.325mm'
        },
        'meander': {
            'asymmetry': '-50um',
            'spacing': '200um'
        },
        'pin_inputs': {
            'end_pin': {
                'component': 'Cap_Q2',
                'pin': 'a'
            },
            'start_pin': {
                'component': 'Q2',
                'pin': 'readout'
            }
        },
        'total_length': '6mm',
        'trace_gap': 'cpw_gap'
    },
    type='CPW',
)

Launch_Q1_Read = LaunchpadWirebond(
    design,
    name='Launch_Q1_Read',
    options={
        'orientation': '180',
        'pos_x': '3.5mm'
    },
    component_template=None,
)

Launch_Q2_Read = LaunchpadWirebond(
    design,
    name='Launch_Q2_Read',
    options={'pos_x': '-3.5mm'},
    component_template=None,
)

Launch_Q1_CL = LaunchpadWirebond(
    design,
    name='Launch_Q1_CL',
    options={
        'orientation': '90',
        'pos_x': '1.35mm',
        'pos_y': '-2.5mm'
    },
    component_template=None,
)

Launch_Q2_CL = LaunchpadWirebond(
    design,
    name='Launch_Q2_CL',
    options={
        'orientation': '-90',
        'pos_x': '-1.35mm',
        'pos_y': '2.5mm'
    },
    component_template=None,
)

TL_Q1 = RoutePathfinder(
    design,
    name='TL_Q1',
    options={
        '_actual_length': '1.0750176727053897 '
                          'mm',
        'fillet': '99um',
        'lead': {
            'end_jogged_extension': '',
            'end_straight': '150um',
            'start_jogged_extension': '',
            'start_straight': '0mm'
        },
        'pin_inputs': {
            'end_pin': {
                'component': 'Cap_Q1',
                'pin': 'b'
            },
            'start_pin': {
                'component': 'Launch_Q1_Read',
                'pin': 'tie'
            }
        },
        'trace_gap': 'cpw_gap'
    },
    type='CPW',
)

TL_Q2 = RoutePathfinder(
    design,
    name='TL_Q2',
    options={
        '_actual_length': '1.0750176727053897 '
                          'mm',
        'fillet': '99um',
        'lead': {
            'end_jogged_extension': '',
            'end_straight': '150um',
            'start_jogged_extension': '',
            'start_straight': '0mm'
        },
        'pin_inputs': {
            'end_pin': {
                'component': 'Cap_Q2',
                'pin': 'b'
            },
            'start_pin': {
                'component': 'Launch_Q2_Read',
                'pin': 'tie'
            }
        },
        'trace_gap': 'cpw_gap'
    },
    type='CPW',
)

TL_Q1_CL = RoutePathfinder(
    design,
    name='TL_Q1_CL',
    options={
        '_actual_length': '2.610508836352695 '
                          'mm',
        'fillet': '99um',
        'lead': {
            'end_jogged_extension': '',
            'end_straight': '150um',
            'start_jogged_extension': '',
            'start_straight': '0mm'
        },
        'pin_inputs': {
            'end_pin': {
                'component': 'Q1',
                'pin': 'Charge_Line'
            },
            'start_pin': {
                'component': 'Launch_Q1_CL',
                'pin': 'tie'
            }
        },
        'trace_gap': 'cpw_gap'
    },
    type='CPW',
)

TL_Q2_CL = RoutePathfinder(
    design,
    name='TL_Q2_CL',
    options={
        '_actual_length': '2.610508836352695 '
                          'mm',
        'fillet': '99um',
        'lead': {
            'end_jogged_extension': '',
            'end_straight': '150um',
            'start_jogged_extension': '',
            'start_straight': '0mm'
        },
        'pin_inputs': {
            'end_pin': {
                'component': 'Q2',
                'pin': 'Charge_Line'
            },
            'start_pin': {
                'component': 'Launch_Q2_CL',
                'pin': 'tie'
            }
        },
        'trace_gap': 'cpw_gap'
    },
    type='CPW',
)

gui.rebuild()
gui.autoscale()
