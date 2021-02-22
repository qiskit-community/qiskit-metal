import pytestqt
import pytest
import hypothesis
import pytest_bdd
import pytest_cov
import inspect
from collections import OrderedDict

from qiskit_metal._gui.widgets.library_new_qcomponent.parameter_entry_scroll_area import ParameterEntryScrollArea
from qiskit_metal import qlibrary
from qiskit_metal.qlibrary.basic.circle_caterpillar import CircleCaterpillar
from qiskit_metal.qlibrary.interconnects.meandered import RouteMeander
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_concentric import TransmonConcentric
from qiskit_metal.qlibrary.basic.n_gon import NGon
from qiskit_metal.qlibrary.passives.launchpad_wb_coupled import LaunchpadWirebondCoupled
from qiskit_metal.qlibrary.interconnects.pathfinder import RoutePathfinder
from qiskit_metal.qlibrary.connectors.cpw_hanger_t import CPWHangerT
from addict.addict import Dict
from qiskit_metal._gui.widgets.library_new_qcomponent.qlibrary_exceptions import PEDASetupException, InvalidParameterEntryException, InvalidFilePathException, LibraryQComponentException, MissingClassException


from datetime import datetime
import numpy as np
import json
from PySide2.QtCore import Qt, QTimer

from PySide2.QtWidgets import QPushButton, QMessageBox
from PySide2 import QtWidgets
from qiskit_metal import designs
import pytest
import importlib
import sys
import pkgutil
import pprint
import inspect
print("CRASH")


# trying to automate for all components
#qubit_mods = inspect.getmembers(qubits, inspect.ismodule)
#print("qubit mods", qubit_mods)
#
#qubit_classes = []
#for entry in qubit_mods:
#    print("entry: ",entry[1])
#    qubit_classes = qubit_classes + inspect.getmembers(entry[1], inspect.isclass)
#
#elms = [(elm[0], inspect.getfile(elm[1])) for elm in qubit_classes ]
#print("elms",elms)
#

@pytest.fixture()
def transmon_additional_options():
    return {
        "pad_width" : '425 um',
        "pocket_height" : '650um',
        "connection_pads":{
            "a"  :{"loc_W":+1,"loc_H":+1},
            "b" : {"loc_W":-1,"loc_H":+1, "pad_height":'30um'},
            "c" : {"loc_W":+1,"loc_H":-1, "pad_width":'200um'},
            "d" : {"loc_W":-1,"loc_H":-1, "pad_height":'50um'}
        }
    }

@pytest.mark.parametrize(
    "test_name, component_file, args_dict",
    [ ("dictionary_empty",  inspect.getfile(TransmonPocket), {}),
      ("dictionary_basic",  inspect.getfile(TransmonPocket), {"name":"mytest", "Chilean":False, "size": 12, "depth":"12uq", "power":0.17}),
      ("dictionary_nested_only",  inspect.getfile(TransmonCross), {"my_nest" : {"n11" : 12, "n12": 0.9, "n13":"astring", "n14": True} } ),
      ("dictionary_nested_w_toplevel_key", inspect.getfile(TransmonCross), {"mykey":"myvalue", "my_nest" : {"n11" : 12, "n12": 0.9, "n13":"astring", "n14": True} } ),
      ("dictionary_2_parallel_nested",  inspect.getfile(TransmonCross), {"my_nest" : {"n11" : 12, "n12": 0.9, "n13":"astring", "n14": True},
                                                                                  "my_nest2": {"n11": 13, "n12": 0.8, "n13": "mystr", "n14":False},
                                                                                  "mykey":"myvalue"} ),
      ("dictionary_nested_4_deep",  inspect.getfile(TransmonCross), {"nest00":
                                                                                             {"nest10":
                                                                                                  {"n20":1, "n21":2, "nest23":
                                                                                                      {"nest30" : {"n40": "cherry"},
                                                                                                       "n31":0.7

                                                                                                       }
                                                                                                   }
                                                                                              }
                                                                                         }
       ),

]
)
def test_create_dictionary(qtbot, test_name, component_file, args_dict): # doesn't test + button :(
    # open ParameterEntryScrollArea w/ abs file path
    # create with different entries (parameterize tests)
    QLIBRARY_ROOT = qlibrary.__name__
    new_design = designs.DesignPlanar()

    ## Create GUI input from dictionary
    pesa = ParameterEntryScrollArea(QLIBRARY_ROOT, component_file, new_design)
    pesa.setup_pesa()
    qtbot.addWidget(pesa)
    entry_count = pesa.parameter_entry_vertical_layout.count()
    a_dictionary = None
    for index in range(entry_count):
        cur_widget = pesa.parameter_entry_vertical_layout.itemAt(index).widget()
        if isinstance(cur_widget, pesa.EntryWidget):
            if isinstance(cur_widget, pesa.DictionaryEntryWidget):
                a_dictionary = cur_widget
    qtbot.addWidget(a_dictionary)

    create_gui_dictionary(qtbot, a_dictionary.all_key_value_pairs_entry_layout, a_dictionary.add_more_button, args_dict)

    ## Create dictionary from GUI input
    new_dict = {}
    pesa.dictionaryentrybox_to_dictionary(a_dictionary.all_key_value_pairs_entry_layout, new_dict)

    ## Compare dictionaries
    assert new_dict == args_dict

    # pp = pprint.PrettyPrinter(indent=4)
    # print("new dict: ")
    # pp.pprint(new_dict)
    # print("para dict:")
    # pp.pprint(args_dict)

    del new_design

@pytest.mark.parametrize(
     "test_name, component_file, args_dict", # these vars will be subset of what real QComponent ends with
    [ ("TransmonPocket-make-true", inspect.getfile(TransmonPocket), {"name":"mytransmon", "make":True}),
       ("TransmonPocket-make-false", inspect.getfile(TransmonPocket), {"name":"mytransmon2", "make":False}),
       ("TransmonCross-make-true",  inspect.getfile(TransmonCross), {"name":"mytransmoncross", "make":True}  ),
       ("TransmonCross-make-false",  inspect.getfile(TransmonCross), {"name": "mytransmoncross2", "make": False}),
       ("TransmonPocket-with-options",inspect.getfile(TransmonPocket), {"name":"transmon-op","options":{"connection_pads":{"a":{}}}}),
       ("TransmonPocket-OptionsQ", inspect.getfile(TransmonPocket),
        {"name":"optionsq",
         "options":{
             "pos_x":'-1.5mm',
             "pos_y":'+0.0mm',
             "pad_width" :'425 um',
             "pocket_height" : '650um',
             "connection_pads" :{  # Qbits defined to have 4 pins
                    "a" : {"loc_W":+1,"loc_H":+1},
                    "b" : {"loc_W":-1,"loc_H":+1, "pad_height":'30um'},
                    "c" : {"loc_W":+1,"loc_H":-1, "pad_width":'200um'},
                    "d" : {"loc_W":-1,"loc_H":-1, "pad_height":'50um'},
                    }
                  }
         }
        )
     ]
)
def test_make_QComponent(qtbot, test_name, component_file, args_dict):
    new_design = designs.DesignPlanar()
    create_qcomponent_via_gui(qtbot, new_design, test_name, component_file, args_dict)
    validate_qcomponent_against_arguments(new_design, test_name, args_dict)
    del(new_design)


@pytest.mark.parametrize(
     "test_name, component_file, args_dict", # these vars will be subset of what real QComponent ends with
    [ ("Basic(NGon)", inspect.getfile(NGon), {"name":"bestNgon",
                                              "options":{
                                                'n':'13',
                                                "radius":'50um',
                                                "pos_x":'1um',
                                                "pos_y":'2um',
                                                "rotation":'3',
                                                "subtract":'False',
                                                "helper":'False',
                                                "chip":'main',
                                                "layer":'1'
                                                }
                                              }
       ),
      ("Connectors(CPWHangerT)", inspect.getfile(CPWHangerT), {"name": "bestCPWHangerT",
                                                               "options": {
                                                                   "prime_width": '10um',
                                                                   "prime_gap": '6um',
                                                                   "second_width": '10um',
                                                                   "second_gap": '6um',
                                                                   "coupling_space": '3um',
                                                                   "coupling_length": '100um',
                                                                   "fillet": '25um',
                                                                   "pos_x": '0um',
                                                                   "pos_y": '0um',
                                                                   "rotation": '0',
                                                                   "mirror": False,
                                                                   "open_termination": True,
                                                                   # Better way to decide this?
                                                                   "chip": 'main',
                                                                   "layer": '1'
                                                               }
                                                               }
       ),
      ("Passives(LaunchpadWirebondCoupled)", inspect.getfile(LaunchpadWirebondCoupled), {"name": "bestLWC",
                                                                                         "options": {
                                                                                             "layer": '1',
                                                                                             "trace_width": 'cpw_width',
                                                                                             "trace_gap": 'cpw_gap',
                                                                                             "coupler_length": '65.5um',
                                                                                             "lead_length": '30um',
                                                                                             "pos_x": '1um',
                                                                                             "pos_y": '2um',
                                                                                             "orientation": '90'
                                                                                         }
                                                                                         }
       ),
      ("Qubits(TransmonConcentric)", inspect.getfile(TransmonConcentric), {"name": "bestTransmonConcentric",
                                                                                         "options": {
                                                                                             "width":'1000um',  # width of transmon pocket
                                                                                             "height":'1000um',
                                                                                             "layer":'1',
                                                                                             "rad_o":'170um',
                                                                                             "rad_i":'115um',
                                                                                             "gap":'35um',
                                                                                             "jj_w":'10um',
                                                                                             "res_s":'100um',
                                                                                             "res_ext":'100um',
                                                                                             "fbl_rad":'100um',
                                                                                             "fbl_sp":'100um',
                                                                                             "fbl_gap":'80um',
                                                                                             "fbl_ext":'300um',
                                                                                             "pocket_w":'1500um',
                                                                                             "pocket_h":'1000um',
                                                                                             "position_x":'2.0mm',
                                                                                             "position_y":'2.0mm',
                                                                                             "rotation":'0.0',
                                                                                             "cpw_width":'10.0um'
                                                                                         }
                                                                            }
       ),
     ]
)
def test_general_QComponent(qtbot, test_name, component_file, args_dict):
    new_design = designs.DesignPlanar()
    create_qcomponent_via_gui(qtbot, new_design, test_name, component_file, args_dict)
    validate_qcomponent_against_arguments(new_design, test_name, args_dict)
    del(new_design)

def anchors(np0, np1):
    ord = OrderedDict()
    ord[0] = np0
    ord[1] = np1
    return ord
@pytest.mark.parametrize(
     "test_name, transmon_file, route_meander_file, transmon_1_args, transmon_2_args, route_meander_args", # these vars will be subset of what real QComponent ends with
    [
        ("Interconnects(RouteMeader)", inspect.getfile(TransmonPocket), inspect.getfile(RouteMeander),
         {"name":"Q1",
          "options" : {"pos_x":'+2.55mm', "pos_y":'+0.0mm',
        "pad_width" : '425 um',
        "pocket_height" : '650um',
        "connection_pads":{
            "a"  :{"loc_W":+1,"loc_H":+1},
            "b" : {"loc_W":-1,"loc_H":+1, "pad_height":'30um'},
            "c" : {"loc_W":+1,"loc_H":-1, "pad_width":'200um'},
            "d" : {"loc_W":-1,"loc_H":-1, "pad_height":'50um'}
        }
    }},
         {"name":"Q2", "options" :
             {"pos_x":'+0.0mm', "pos_y":'-0.9mm', "pad_width" : '425 um', "pocket_height" : '650um',"connection_pads":{
            "a"  :{"loc_W":+1,"loc_H":+1},
            "b" : {"loc_W":-1,"loc_H":+1, "pad_height":'30um'},
            "c" : {"loc_W":+1,"loc_H":-1, "pad_width":'200um'},
            "d" : {"loc_W":-1,"loc_H":-1, "pad_height":'50um'}
        }}},{
       "name":"bestRouteMeander", "options":{'pin_inputs': {'start_pin': {'component': 'Q1', 'pin': 'd'}, 'end_pin': {'component': 'Q2', 'pin': 'c'}}, 'lead': {'start_straight': '0.13mm'}, 'total_length': '6.0 mm', 'fillet': '90um', 'meander': {'lead_start': '0.1mm', 'lead_end': '0.1mm', 'asymmetry': '+150um'}}
       }),

        ("Interconnects(RoutePathfinder)", inspect.getfile(TransmonPocket), inspect.getfile(RoutePathfinder),
         {"name": "Q1",
          "options": {"pos_x": '+2.55mm', "pos_y": '+0.0mm',
                                    "pad_width": '425 um',
                                    "pocket_height": '650um',
                                    "connection_pads": {
                                        "a": {"loc_W": +1, "loc_H": +1},
                                        "b": {"loc_W": -1, "loc_H": +1, "pad_height": '30um'},
                                        "c": {"loc_W": +1, "loc_H": -1, "pad_width": '200um'},
                                        "d": {"loc_W": -1, "loc_H": -1, "pad_height": '50um'}
                                    }
                                    }},
         {"name": "Q2",
            "options": {"pos_x": '+0.0mm', "pos_y": '-0.9mm', "pad_width": '425 um',
                                                     "pocket_height": '650um', "connection_pads": {
                                                 "a": {"loc_W": +1, "loc_H": +1},
                                                 "b": {"loc_W": -1, "loc_H": +1, "pad_height": '30um'},
                                                 "c": {"loc_W": +1, "loc_H": -1, "pad_width": '200um'},
                                                 "d": {"loc_W": -1, "loc_H": -1, "pad_height": '50um'}
                                             }}}, {
             "name": "bestRoutePathFinder", "options": {
                'pin_inputs': {
                    'start_pin': {'component': 'Q1', 'pin': 'b'},
                    'end_pin': {'component': 'Q2', 'pin': 'b'}
                },
                'lead':  {'start_straight': '91um', 'end_straight': '90um'},
                'step_size': '0.25mm',
                'anchors': anchors(np.array([0.048, -0.555]), np.array([0.048, -0.555])),
                'fillet': '90um',
         }}),

        ("Interconnects(RoutePathfinder)", inspect.getfile(TransmonPocket), inspect.getfile(RoutePathfinder),
         {"name": "Q1",
          "options": {"pos_x": '+2.55mm', "pos_y": '+0.0mm',
                      "pad_width": '425 um',
                      "pocket_height": '650um',
                      "connection_pads": {
                          "a": {"loc_W": +1, "loc_H": +1},
                          "b": {"loc_W": -1, "loc_H": +1, "pad_height": '30um'},
                          "c": {"loc_W": +1, "loc_H": -1, "pad_width": '200um'},
                          "d": {"loc_W": -1, "loc_H": -1, "pad_height": '50um'}
                      }
                      }},
         {"name": "Q2",
          "options": {"pos_x": '+0.0mm', "pos_y": '-0.9mm', "pad_width": '425 um',
                      "pocket_height": '650um', "connection_pads": {
                  "a": {"loc_W": +1, "loc_H": +1},
                  "b": {"loc_W": -1, "loc_H": +1, "pad_height": '30um'},
                  "c": {"loc_W": +1, "loc_H": -1, "pad_width": '200um'},
                  "d": {"loc_W": -1, "loc_H": -1, "pad_height": '50um'}
              }}}, {
             "name": "bestRoutePathFinder", "options": {
                'pin_inputs': {
                    'start_pin': {'component': 'Q1', 'pin': 'b'},
                    'end_pin': {'component': 'Q2', 'pin': 'b'}
                },
                'lead': {'start_straight': '91um', 'end_straight': '90um'},
                'step_size': '0.25mm',
                'anchors': anchors(np.array([0.048, -0.555]), np.array([0.048, -0.555])),
                'fillet': '90um',
            }}),


    ]
)
def test_general_connecters(qtbot, test_name, transmon_file, route_meander_file, transmon_1_args, transmon_2_args, route_meander_args):
    #create transmons then add connections
    new_design = designs.DesignPlanar()
    create_qcomponent_via_gui(qtbot, new_design, test_name, transmon_file, transmon_1_args)
    create_qcomponent_via_gui(qtbot, new_design, test_name, transmon_file, transmon_2_args)
    create_qcomponent_via_gui(qtbot, new_design, test_name, route_meander_file, route_meander_args) # requires other two qubits to be made before can be created
    validate_qcomponent_against_arguments(new_design, test_name, transmon_1_args)
    validate_qcomponent_against_arguments(new_design, test_name, transmon_2_args)
    validate_qcomponent_against_arguments(new_design, test_name, route_meander_args)

def create_qcomponent_via_gui(qtbot, new_design, test_name, component_file, args_dict):
    # open ParameterEntryScrollArea w/ abs file path
    # create with different entries (parameterize testsV
    QLIBRARY_ROOT = qlibrary.__name__
    pesa = ParameterEntryScrollArea(QLIBRARY_ROOT, component_file, new_design)
    pesa.setup_pesa()
    qtbot.addWidget(pesa)
    pesa.parameter_entry_vertical_layout
    entry_count = pesa.parameter_entry_vertical_layout.count()
    for index in range(entry_count):
        cur_widget = pesa.parameter_entry_vertical_layout.itemAt(index).widget()
        if isinstance(cur_widget, pesa.EntryWidget):
            if cur_widget.arg_name in args_dict:
                if isinstance(cur_widget, pesa.NormalEntryWidget):
                    cur_widget.value_edit.setText(str(args_dict[cur_widget.arg_name]))
                elif isinstance(cur_widget, ParameterEntryScrollArea.DictionaryEntryWidget):
                    qtbot.add_widget(cur_widget)
                    create_gui_dictionary(qtbot, cur_widget.all_key_value_pairs_entry_layout,
                                           cur_widget.add_more_button, args_dict[cur_widget.arg_name])
    qtbot.addWidget(pesa.make_button)
    qtbot.mouseClick(pesa.make_button, Qt.LeftButton)
    # pesa should get deleted since make button has been called

def validate_qcomponent_against_arguments(new_design, test_name, args_dict):
    qcomponent = new_design.components[args_dict["name"]]

    for k,v in args_dict.items():
        if k == "make": #must come first because there is `make` method in every object that would show up in `hasattr` in addition to the boolean `make` parameter
            print(k,"k is make")
            if args_dict[k]:
                assert qcomponent._made
            else:
                assert qcomponent._made == False
        elif hasattr(qcomponent, k):
            print("has ", k)
            if type(args_dict[k]) is dict:
               qcomponent_v = getattr(qcomponent, k)
               param_v = args_dict[k]
               compare_subset(qcomponent_v, param_v)

            else:
                assert getattr(qcomponent, k) == args_dict[k]
        elif hasattr(qcomponent, "_" + k):
            print("has _", k)
            assert getattr(qcomponent, "_" + k) == args_dict[k]
        else:
            print("MISSING QCOMP: ", qcomponent)
            print("MISSING ATRIBUTE: ", qcomponent.__dict__)
            raise Exception("MISSING ATTRIBUTE: ", k)

def compare_subset(qcomponent_v, param_v):
    for k in param_v.keys():
        if type(param_v[k]) is dict or type(param_v[k]) is Dict or type(param_v[k]) is OrderedDict:
            # Ordered Dictionaries do NOT stay ordered dictionaries in Routing - not sure why
            compare_subset(qcomponent_v[k], param_v[k]) #will error if k is missing in qcomponent
        else:
            print(f"k: {k}")
            print(f"param_v[k]: {param_v[k]}")
            if isinstance(param_v[k], type(np.array([]))):
                print(f"k: {k}")
                print(f"param_v[k]: {param_v[k]}")
                assert (param_v[k]==qcomponent_v[k]).all() #compare each index of numpy array
            else:
                assert param_v[k] == qcomponent_v[k]

def create_gui_dictionary(qtbot, dict_box_layout, add_box_button: QPushButton, param_dict: dict):
    if param_dict == {}:
        return
    # {key: value,
    #    key: {k2 : value}
    # }
    #set type, nest, etc

    qtbot.addWidget(add_box_button)
    count = 1 # start at first possible box. 0 is "+"
    for key,value in param_dict.items():

        # get/create dictbox for entry
        if dict_box_layout.itemAt(count) is None:
            qtbot.mouseClick(add_box_button, Qt.LeftButton)
        cur_box = dict_box_layout.itemAt(count).widget()
        count += 1
        qtbot.addWidget(cur_box)

        # see type
        v_type = type(value)
        cur_box.name_o.setText(str(key))
        if v_type != dict and v_type != Dict and v_type != OrderedDict:
            print("\nnewkey: ", cur_box.name_o.text())
            if v_type is type(np.array([])):
                value = json.dumps(list(value))
            cur_box.value_o.setText(str(value))
            cur_box.type_name.setCurrentText(v_type.__name__)
        else:
            print("clicking nest")
            qtbot.mouseClick(cur_box.nested_dict_button, Qt.LeftButton) #should turn value_o into dictBox inside of the self.sub_entry_collapsable
            cur_box.type_name.setCurrentText(v_type.__name__)
            print(f"setting box layer dict type to: {v_type.__name__}")

            assert isinstance(cur_box.value_o, ParameterEntryScrollArea.DictionaryEntryWidget.DictionaryEntryBox)
            create_gui_dictionary(qtbot, cur_box.nested_dictionary.nested_kv_layout, cur_box.nested_dictionary.add_more_button, value)
