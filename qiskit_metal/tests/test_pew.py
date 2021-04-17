# from collections import OrderedDict
# from qiskit_metal import qlibrary
# from qiskit_metal.qlibrary.interconnects.meandered import RouteMeander
# from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
# from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
# from qiskit_metal.qlibrary.qubits.transmon_concentric import TransmonConcentric
# from qiskit_metal.qlibrary.basic.n_gon import NGon
# from qiskit_metal.qlibrary.passives.launchpad_wb_coupled import LaunchpadWirebondCoupled
# from qiskit_metal.qlibrary.interconnects.pathfinder import RoutePathfinder
# from qiskit_metal.qlibrary.connectors.cpw_hanger_t import CPWHangerT
# from qiskit_metal._gui.widgets.create_component_window import parameter_entry_window as pew
# from qiskit_metal._gui.widgets.create_component_window.model_view.tree_model_param_entry import BranchNode
# from qiskit_metal import MetalGUI
# from addict.addict import Dict
# from PySide2 import QtCore
# from PySide2.QtGui import QFont
# from PySide2.QtWidgets import QTreeView, QWidget
# from PySide2.QtCore import QAbstractItemModel, QModelIndex, QTimer, Qt
# import ast
# from typing import Union, TYPE_CHECKING
# import queue
# from PySide2.QtCore import QAbstractItemModel, QModelIndex, QTimer, Qt
# from PySide2.QtWidgets import (QAbstractItemView, QApplication, QFileDialog,
#                                QWidget, QTreeView, QLabel, QMainWindow,
#                                QMessageBox, QTabWidget, QComboBox)
# from collections import OrderedDict
# from addict import Dict
#
# import numpy as np
# import json
# import builtins
#
# import numpy as np
# import json
# from PySide2.QtCore import Qt
# import logging
# logging.basicConfig(level=logging.DEBUG)
# mylogger = logging.getLogger()
#
# from PySide2.QtWidgets import QPushButton
# from qiskit_metal import designs
# import pytest
# import inspect
# import unittest
#
#
#
# class TestPew(unittest.TestCase):
#
#     @classmethod
#     def setUpClass(cls) -> None:
#         from qiskit_metal import MetalGUI, Dict, open_docs
#         design = designs.DesignPlanar()
#         cls.gui = MetalGUI(design)
#
#     @classmethod
#     def tearDownClass(cls) -> None:
#         #cls.gui.main_window.close()
#         cls.gui.qApp.setQuitOnLastWindowClosed(True)
#
#         cls.gui.main_window.set_force_close(True)
#
#         cls.gui.main_window.close()
#         #cls.gui.qApp.closeAllWindows()
#         #cls.gui.qApp.closingDown()
#
#     def anchors(self,np0, np1):
#         ord = OrderedDict()
#         ord[0] = np0
#         ord[1] = np1
#         return ord
#
#
#     #RouteMixed(design, 'line', optionsR)
#     def complicated_route_mixed(self):
#         anchors = OrderedDict()
#         anchors[0] = np.array([-3., 1.])
#         anchors[1] = np.array([0, 2])
#         anchors[2] = np.array([3., 1])
#         anchors[3] = np.array([4., .5])
#
#         between_anchors = OrderedDict()  # S, M, PF
#         between_anchors[0] = "S"
#         between_anchors[1] = "M"
#         between_anchors[2] = "S"
#         between_anchors[3] = "M"
#         between_anchors[4] = "S"
#
#         jogsS = OrderedDict()
#         jogsS[0] = ["R", '200um']
#         jogsS[1] = ["R", '200um']
#         jogsS[2] = ["L", '200um']
#         jogsS[3] = ["L", '500um']
#         jogsS[4] = ["R", '200um']
#
#         jogsE = OrderedDict()
#         jogsE[0] = ["L", '200um']
#         jogsE[1] = ["L", '200um']
#         jogsE[2] = ["R", '200um']
#         jogsE[3] = ["R", '500um']
#         jogsE[4] = ["L", '200um']
#
#         ops = dict(fillet='90um')
#
#         data = {
#             'pin_inputs': {
#                 'start_pin': {
#                     'component': 'Q0',
#                     'pin': 'a'
#                 },
#                 'end_pin': {
#                     'component': 'Q1',
#                     'pin': 'a'
#                 }
#             },
#             'total_length': '32mm',
#             'chip': 'main',
#             'layer': '1',
#             'trace_width': 'cpw_width',
#             'step_size': '0.25mm',
#             'anchors': anchors,
#             'between_anchors': between_anchors,
#             'advanced': {
#                 'avoid_collision': 'true'
#             },
#             'meander': {
#                 'spacing': '200um',
#                 'asymmetry': '0um'
#             },
#             'snap': 'true',
#             'lead': {
#                 'start_straight': '0.3mm',
#                 'end_straight': '0.3mm',
#                 'start_jogged_extension': jogsS,
#                 'end_jogged_extension': jogsE
#             },
#             **ops
#         }
#         return data
#
#
#     def complicated_route_mixed_2(self):
#         anchors = OrderedDict()
#         anchors[0] = np.array([-3., 1.])
#         anchors[1] = np.array([0, 2])
#         anchors[2] = np.array([3., 1])
#         anchors[3] = np.array([4., .5])
#
#         between_anchors = OrderedDict()  # S, M, PF
#         between_anchors[0] = "S"
#         between_anchors[1] = "M"
#         between_anchors[2] = "PF"
#         between_anchors[3] = "M"
#         between_anchors[4] = "S"
#
#         jogsS = OrderedDict()
#         jogsS[0] = ["R", '800um']
#         jogsS[1] = ["R", '800um']
#         jogsS[2] = ["L", '800um']
#         jogsS[3] = ["L", '800um']
#         jogsS[4] = ["R", '800um']
#
#         jogsE = OrderedDict()
#         jogsE[0] = ["L", '200um']
#         jogsE[1] = ["L", '200um']
#         jogsE[2] = ["R", '200um']
#         jogsE[3] = ["R", '500um']
#         jogsE[4] = ["L", '200um']
#
#         ops = dict(fillet='90um')
#
#         data = {
#             'pin_inputs': {
#                 'start_pin': {
#                     'component': 'Q0',
#                     'pin': 'a'
#                 },
#                 'end_pin': {
#                     'component': 'Q1',
#                     'pin': 'a'
#                 }
#             },
#             'total_length': '320um',
#             'chip': 'main',
#             'layer': '1',
#             'trace_width': 'cpw_width',
#             'step_size': '0.25mm',
#             'anchors': anchors,
#             'between_anchors': between_anchors,
#             'advanced': {
#                 'avoid_collision': 'true'
#             },
#             'meander': {
#                 'spacing': '200um',
#                 'asymmetry': '0um'
#             },
#             'snap': 'true',
#             'lead': {
#                 'start_straight': '0.3mm',
#                 'end_straight': '0.3mm',
#                 'start_jogged_extension': jogsS,
#                 'end_jogged_extension': jogsE
#             },
#             **ops
#         }
#         return data
#
#
#     #
#     # @pytest.mark.parametrize(
#     #      "test_name, qcomp, update_args", # these vars will be subset of what real QComponent ends with
#     #      [
#     #          ("TransmonPocket", TransmonPocket,
#     #                                                               {"name": "bettertransmon", "make": False}),
#     #          ("TransmonCross-make-false",   TransmonCross,
#     #                                                         {"name": "BESTCROSS", "make": True}),
#     #          ("TransmonPocket-with-options",TransmonPocket,
#     #                                                                         {"name": "COOLTransmon","options": {"connection_pads": {"b" : {"loc_W": +2,"loc_H": +1}}}})
#     #      ]
#     # )
#     # def test_simple_manual_edits(test_name, qcomp, args_dict):
#     #     new_design = designs.DesignPlanar()
#     #     param_window = pew.ParameterEntryWindow(qcomp, new_design)
#     #     param_window.setup_pew()
#     #     rootindex = param_window.model.index(0, 0, QModelIndex())
#     #
#     #
#     # def add_items(parent_node: pew.Node, args_dict: dict):
#     #     if isinstance(parent_node, pew.LeafNode):
#     #         if len(args_dict) > 1:
#     #             raise Exception(f"{args_dict} is too large for: {parent_node}")
#     #         for k in args_dict.keys():
#     #             if k == parent_node.name
#     #
#     #     found = False
#     #     for top_level_key in args_dict.keys():
#     #         for child_name, child_node in parent_node.children:
#     #             if top_level_key == child_name:
#     #                 found = True
#     #                 add_items(child_node, args_dict[top_level_key])
#     #         if not found:
#     #             if type(args_dict[top_level_key] in pew.BranchNode.BranchTypeComboBox.branch_types):
#     #                 branch = pew.BranchNode(top_level_key,parent_node, type(args_dict[top_level_key]))
#     #                 parent_node.insertChild(branch)
#     #                 add_items(branch, args_dict[top_level_key])
#     #             else:
#     #                 parent_node.insertChild(pew.LeafNode(top_level_key, args_dict[top_level_key]))
#     #
#     #
#     #
#
#     #TODO test editing keys
#
#
#     def transmon_additional_options(self):
#         return {
#             "pad_width": '425 um',
#             "pocket_height": '650um',
#             "connection_pads": {
#                 "a": {
#                     "loc_W": +1,
#                     "loc_H": +1
#                 },
#                 "b": {
#                     "loc_W": -1,
#                     "loc_H": +1,
#                     "pad_height": '30um'
#                 },
#                 "c": {
#                     "loc_W": +1,
#                     "loc_H": -1,
#                     "pad_width": '200um'
#                 },
#                 "d": {
#                     "loc_W": -1,
#                     "loc_H": -1,
#                     "pad_height": '50um'
#                 }
#             }
#         }
#
#     #     "args_dict", # these vars will be subset of what real QComponent ends with
#
#
#     def test_pew_model_to_dict(self):
#         args_dict = [{"name": "mytransmon"},
#                      {"name": "mytransmoncross", "make": True},
#                      {"name": "mytransmoncross2", "options": {"anchors": self.anchors(1, 2)}},
#
#                         {"name": "optionsq",
#                          "options": {
#                              "pos_x": '-1.5mm',
#                              "pos_y": '+0.0mm',
#                              "pad_width": '425 um',
#                              "pocket_height": '650um',
#                              "connection_pads": {  # Qbits defined to have 4 pins
#                                  "a": {"loc_W": +1, "loc_H": +1},
#                                  "b": {"loc_W": -1, "loc_H": +1, "pad_height": '30um'},
#                                  "c": {"loc_W": +1, "loc_H": -1, "pad_width": '200um'},
#                                  "d": {"loc_W": -1, "loc_H": -1, "pad_height": '50um'},
#                              }
#                          }
#                          }
#
#                      ]
#         for test_dict in args_dict:
#             self.pew_model_to_dict_helper(test_dict)
#
#     def pew_model_to_dict_helper(self, test_dict):
#         new_design = designs.DesignPlanar()
#         param_window = pew.ParameterEntryWindow(TransmonConcentric, new_design)
#         param_window.setup_pew()
#         param_window.model.init_load(
#             test_dict)  #reload entire model and use only args_dic
#         param_window.traverse_model_to_create_dictionary()
#         assert param_window.current_dict == test_dict
#
#     def test_general_qcomponent_make_param(self):
#
#         #   "test_name, component_file, args_dict", # these vars will be subset of what real QComponent ends with
#         tests_args =  [  ("TransmonPocket-make-true", inspect.getfile(TransmonPocket), {"name": "mytransmon", "make": True}),
#            ("TransmonPocket-make-false", inspect.getfile(TransmonPocket), {"name": "mytransmon2", "make": False}),
#            ("TransmonCross-make-true",  inspect.getfile(TransmonCross), {"name": "mytransmoncross", "make": True}  ),
#            ("TransmonCross-make-false",  inspect.getfile(TransmonCross), {"name": "mytransmoncross2", "make": False}),
#            ("TransmonPocket-with-options",inspect.getfile(TransmonPocket), {"name": "transmon-op","options": {"connection_pads": {"a" : {"loc_W": +1,"loc_H": +1}}}}),
#            ("TransmonPocket-OptionsQ", inspect.getfile(TransmonPocket),
#             {"name": "optionsq",
#              "options": {
#                  "pos_x": '-1.5mm',
#                  "pos_y": '+0.0mm',
#                  "pad_width" : '425 um',
#                  "pocket_height" : '650um',
#                  "connection_pads" : {  # Qbits defined to have 4 pins
#                         "a" : {"loc_W": +1,"loc_H": +1},
#                         "b" : {"loc_W": -1,"loc_H": +1, "pad_height": '30um'},
#                         "c" : {"loc_W": +1,"loc_H": -1, "pad_width": '200um'},
#                         "d" : {"loc_W": -1,"loc_H": -1, "pad_height": '50um'},
#                         }
#                       }
#              }
#             )
#          ]
#
#         for args in tests_args:
#             self.general_qcomponent_make_param_helper(*args)
#
#     def general_qcomponent_make_param_helper(self,test_name, component_file,
#                              args_dict ):
#         new_design = designs.DesignPlanar()
#         create_qcomp_via_pew(qtbot, new_design, test_name, component_file,
#                              args_dict)
#         new_design = designs.DesignPlanar()
#         create_qcomp_via_pew(qtbot, new_design, test_name, component_file,
#                              args_dict)
#         validate_qcomp(new_design, test_name, args_dict)
#         print(
#             f"Given:\n {args_dict}\nGotten:\n{new_design.components[args_dict['name']].__dict__}"
#         )
#         del (new_design)
#
#
#     @pytest.mark.parametrize(
#         "test_name, transmon_file, route_meander_file, transmon_1_args, transmon_2_args, route_meander_args",  # these vars will be subset of what real QComponent ends with
#         [
#             ("Interconnects(RouteMeader)", inspect.getfile(TransmonPocket),
#              inspect.getfile(RouteMeander), {
#                  "name": "Q1",
#                  "options": {
#                      "pos_x": '+2.55mm',
#                      "pos_y": '+0.0mm',
#                      "pad_width": '425 um',
#                      "pocket_height": '650um',
#                      "connection_pads": {
#                          "a": {
#                              "loc_W": +1,
#                              "loc_H": +1
#                          },
#                          "b": {
#                              "loc_W": -1,
#                              "loc_H": +1,
#                              "pad_height": '30um'
#                          },
#                          "c": {
#                              "loc_W": +1,
#                              "loc_H": -1,
#                              "pad_width": '200um'
#                          },
#                          "d": {
#                              "loc_W": -1,
#                              "loc_H": -1,
#                              "pad_height": '50um'
#                          }
#                      }
#                  }
#              }, {
#                  "name": "Q2",
#                  "options": {
#                      "pos_x": '+0.0mm',
#                      "pos_y": '-0.9mm',
#                      "pad_width": '425 um',
#                      "pocket_height": '650um',
#                      "connection_pads": {
#                          "a": {
#                              "loc_W": +1,
#                              "loc_H": +1
#                          },
#                          "b": {
#                              "loc_W": -1,
#                              "loc_H": +1,
#                              "pad_height": '30um'
#                          },
#                          "c": {
#                              "loc_W": +1,
#                              "loc_H": -1,
#                              "pad_width": '200um'
#                          },
#                          "d": {
#                              "loc_W": -1,
#                              "loc_H": -1,
#                              "pad_height": '50um'
#                          }
#                      }
#                  }
#              }, {
#                  "name": "bestRouteMeander",
#                  "options": {
#                      'pin_inputs': {
#                          'start_pin': {
#                              'component': 'Q1',
#                              'pin': 'd'
#                          },
#                          'end_pin': {
#                              'component': 'Q2',
#                              'pin': 'c'
#                          }
#                      },
#                      'lead': {
#                          'start_straight': '0.13mm'
#                      },
#                      'total_length': '6.0 mm',
#                      'fillet': '90um',
#                      'meander': {
#                          'lead_start': '0.1mm',
#                          'lead_end': '0.1mm',
#                          'asymmetry': '+150um'
#                      }
#                  }
#              }),
#             ("Interconnects(RoutePathfinder)", inspect.getfile(TransmonPocket),
#              inspect.getfile(RoutePathfinder), {
#                  "name": "Q1",
#                  "options": {
#                      "pos_x": '+2.55mm',
#                      "pos_y": '+0.0mm',
#                      "pad_width": '425 um',
#                      "pocket_height": '650um',
#                      "connection_pads": {
#                          "a": {
#                              "loc_W": +1,
#                              "loc_H": +1
#                          },
#                          "b": {
#                              "loc_W": -1,
#                              "loc_H": +1,
#                              "pad_height": '30um'
#                          },
#                          "c": {
#                              "loc_W": +1,
#                              "loc_H": -1,
#                              "pad_width": '200um'
#                          },
#                          "d": {
#                              "loc_W": -1,
#                              "loc_H": -1,
#                              "pad_height": '50um'
#                          }
#                      }
#                  }
#              }, {
#                  "name": "Q2",
#                  "options": {
#                      "pos_x": '+0.0mm',
#                      "pos_y": '-0.9mm',
#                      "pad_width": '425 um',
#                      "pocket_height": '650um',
#                      "connection_pads": {
#                          "a": {
#                              "loc_W": +1,
#                              "loc_H": +1
#                          },
#                          "b": {
#                              "loc_W": -1,
#                              "loc_H": +1,
#                              "pad_height": '30um'
#                          },
#                          "c": {
#                              "loc_W": +1,
#                              "loc_H": -1,
#                              "pad_width": '200um'
#                          },
#                          "d": {
#                              "loc_W": -1,
#                              "loc_H": -1,
#                              "pad_height": '50um'
#                          }
#                      }
#                  }
#              }, {
#                  "name": "bestRoutePathFinder",
#                  "options": {
#                      'pin_inputs': {
#                          'start_pin': {
#                              'component': 'Q1',
#                              'pin': 'b'
#                          },
#                          'end_pin': {
#                              'component': 'Q2',
#                              'pin': 'b'
#                          }
#                      },
#                      'lead': {
#                          'start_straight': '91um',
#                          'end_straight': '90um'
#                      },
#                      'step_size':
#                          '0.25mm',
#                      'anchors':
#                          anchors(np.array([0.048, -0.555]), np.array(
#                              [0.048, -0.555])),
#                      'fillet':
#                          '90um',
#                  }
#              }),
#             ("Interconnects(RoutePathfinder)", inspect.getfile(TransmonPocket),
#              inspect.getfile(RoutePathfinder), {
#                  "name": "Q1",
#                  "options": {
#                      "pos_x": '+2.55mm',
#                      "pos_y": '+0.0mm',
#                      "pad_width": '425 um',
#                      "pocket_height": '650um',
#                      "connection_pads": {
#                          "a": {
#                              "loc_W": +1,
#                              "loc_H": +1
#                          },
#                          "b": {
#                              "loc_W": -1,
#                              "loc_H": +1,
#                              "pad_height": '30um'
#                          },
#                          "c": {
#                              "loc_W": +1,
#                              "loc_H": -1,
#                              "pad_width": '200um'
#                          },
#                          "d": {
#                              "loc_W": -1,
#                              "loc_H": -1,
#                              "pad_height": '50um'
#                          }
#                      }
#                  }
#              }, {
#                  "name": "Q2",
#                  "options": {
#                      "pos_x": '+0.0mm',
#                      "pos_y": '-0.9mm',
#                      "pad_width": '425 um',
#                      "pocket_height": '650um',
#                      "connection_pads": {
#                          "a": {
#                              "loc_W": +1,
#                              "loc_H": +1
#                          },
#                          "b": {
#                              "loc_W": -1,
#                              "loc_H": +1,
#                              "pad_height": '30um'
#                          },
#                          "c": {
#                              "loc_W": +1,
#                              "loc_H": -1,
#                              "pad_width": '200um'
#                          },
#                          "d": {
#                              "loc_W": -1,
#                              "loc_H": -1,
#                              "pad_height": '50um'
#                          }
#                      }
#                  }
#              }, {
#                  "name": "bestRoutePathFinder",
#                  "options": {
#                      'pin_inputs': {
#                          'start_pin': {
#                              'component': 'Q1',
#                              'pin': 'b'
#                          },
#                          'end_pin': {
#                              'component': 'Q2',
#                              'pin': 'b'
#                          }
#                      },
#                      'lead': {
#                          'start_straight': '91um',
#                          'end_straight': '90um'
#                      },
#                      'step_size':
#                          '0.25mm',
#                      'anchors':
#                          anchors(np.array([0.048, -0.555]), np.array(
#                              [0.048, -0.555])),
#                      'fillet':
#                          '90um',
#                  }
#              }),
#         ])
#     def test_general_connecters(qtbot, test_name, transmon_file, route_meander_file,
#                                 transmon_1_args, transmon_2_args,
#                                 route_meander_args):
#         #create transmons then add connections
#         new_design = designs.DesignPlanar()
#         create_qcomp_via_pew(qtbot, new_design, test_name, transmon_file,
#                              transmon_1_args)
#         create_qcomp_via_pew(qtbot, new_design, test_name, transmon_file,
#                              transmon_2_args)
#         create_qcomp_via_pew(
#             qtbot, new_design, test_name, route_meander_file, route_meander_args
#         )  # requires other two qubits to be made before can be created
#         validate_qcomp(new_design, test_name, transmon_1_args)
#         validate_qcomp(new_design, test_name, transmon_2_args)
#         validate_qcomp(new_design, test_name, route_meander_args)
#
#
#     @pytest.mark.parametrize(
#         "test_name, component_file, args_dict",  # these vars will be subset of what real QComponent ends with
#         [
#             ("Basic(NGon)", inspect.getfile(NGon), {
#                 "name": "bestNgon",
#                 "options": {
#                     'n': '13',
#                     "radius": '50um',
#                     "pos_x": '1um',
#                     "pos_y": '2um',
#                     "rotation": '3',
#                     "subtract": 'False',
#                     "helper": 'False',
#                     "chip": 'main',
#                     "layer": '1'
#                 }
#             }),
#             (
#                 "Connectors(CPWHangerT)",
#                 inspect.getfile(CPWHangerT),
#                 {
#                     "name": "bestCPWHangerT",
#                     "options": {
#                         "prime_width": '10um',
#                         "prime_gap": '6um',
#                         "second_width": '10um',
#                         "second_gap": '6um',
#                         "coupling_space": '3um',
#                         "coupling_length": '100um',
#                         "fillet": '25um',
#                         "pos_x": '0um',
#                         "pos_y": '0um',
#                         "rotation": '0',
#                         "mirror": False,
#                         "open_termination": True,
#                         # Better way to decide this?
#                         "chip": 'main',
#                         "layer": '1'
#                     }
#                 }),
#             ("Passives(LaunchpadWirebondCoupled)",
#              inspect.getfile(LaunchpadWirebondCoupled), {
#                  "name": "bestLWC",
#                  "options": {
#                      "layer": '1',
#                      "trace_width": 'cpw_width',
#                      "trace_gap": 'cpw_gap',
#                      "coupler_length": '65.5um',
#                      "lead_length": '30um',
#                      "pos_x": '1um',
#                      "pos_y": '2um',
#                      "orientation": '90'
#                  }
#              }),
#             (
#                 "Qubits(TransmonConcentric)",
#                 inspect.getfile(TransmonConcentric),
#                 {
#                     "name": "bestTransmonConcentric",
#                     "options": {
#                         "width": '1000um',  # width of transmon pocket
#                         "height": '1000um',
#                         "layer": '1',
#                         "rad_o": '170um',
#                         "rad_i": '115um',
#                         "gap": '35um',
#                         "jj_w": '10um',
#                         "res_s": '100um',
#                         "res_ext": '100um',
#                         "fbl_rad": '100um',
#                         "fbl_sp": '100um',
#                         "fbl_gap": '80um',
#                         "fbl_ext": '300um',
#                         "pocket_w": '1500um',
#                         "pocket_h": '1000um',
#                         "position_x": '2.0mm',
#                         "position_y": '2.0mm',
#                         "rotation": '0.0',
#                         "cpw_width": '10.0um'
#                     }
#                 }),
#         ])
#     def test_general_QComponent(qtbot, test_name, component_file, args_dict):
#         new_design = designs.DesignPlanar()
#         create_qcomp_via_pew(qtbot, new_design, test_name, component_file,
#                              args_dict)
#         validate_qcomp(new_design, test_name, args_dict)
#         del (new_design)
#
#
#     @pytest.mark.parametrize(
#         "test_name, component_file1, component_file2, component_file3, args1, args2, args3",  # these vars will be subset of what real QComponent ends with
#         [
#             (
#                 "Ngon-CPWHangerT-LaunchpadWirebondCoupled",
#                 inspect.getfile(NGon),
#                 inspect.getfile(CPWHangerT),
#                 inspect.getfile(LaunchpadWirebondCoupled),
#                 {
#                     "name": "bestNgon",
#                     "options": {
#                         'n': '13',
#                         "radius": '50um',
#                         "pos_x": '1um',
#                         "pos_y": '2um',
#                         "rotation": '3',
#                         "subtract": 'False',
#                         "helper": 'False',
#                         "chip": 'main',
#                         "layer": '1'
#                     }
#                 },
#                 {
#                     "name": "bestCPWHangerT",
#                     "options": {
#                         "prime_width": '10um',
#                         "prime_gap": '6um',
#                         "second_width": '10um',
#                         "second_gap": '6um',
#                         "coupling_space": '3um',
#                         "coupling_length": '100um',
#                         "fillet": '25um',
#                         "pos_x": '0um',
#                         "pos_y": '0um',
#                         "rotation": '0',
#                         "mirror": False,
#                         "open_termination": True,
#                         # Better way to decide this?
#                         "chip": 'main',
#                         "layer": '1'
#                     }
#                 },
#                 {
#                     "name": "bestLWC",
#                     "options": {
#                         "layer": '1',
#                         "trace_width": 'cpw_width',
#                         "trace_gap": 'cpw_gap',
#                         "coupler_length": '65.5um',
#                         "lead_length": '30um',
#                         "pos_x": '1um',
#                         "pos_y": '2um',
#                         "orientation": '90'
#                     }
#                 }),
#         ])
#     def test_multiple_Qcomponents(qtbot, test_name, component_file1,
#                                   component_file2, component_file3, args1, args2,
#                                   args3):
#         design = designs.DesignPlanar()
#         create_qcomp_via_pew(qtbot, design, test_name, component_file1, args1)
#         create_qcomp_via_pew(qtbot, design, test_name, component_file2, args2)
#         create_qcomp_via_pew(qtbot, design, test_name, component_file3, args3)
#         validate_qcomp(design, test_name, args1)
#         validate_qcomp(design, test_name, args2)
#         validate_qcomp(design, test_name, args3)
#         del (design)
#
#
#     def create_qcomp_via_pew(qtbot, new_design, test_name, component_file,
#                              args_dict):
#         cur_class = pew.get_class_from_abs_file_path(component_file)
#         param_window = pew.ParameterEntryWindow(cur_class, new_design)
#         param_window.setup_pew()
#         param_window.model.init_load(
#             args_dict)  #reload entire model and use only args_dict
#         qtbot.addWidget(param_window.ui.create_qcomp_button)
#         qtbot.mouseClick(param_window.ui.create_qcomp_button, Qt.LeftButton)
#
#
#     def validate_qcomp(new_design: designs.DesignPlanar, test_name, args_dict):
#         qcomponent = new_design.components[args_dict["name"]]
#
#         for k, v in args_dict.items():
#             if k == "make":  #must come first because there is `make` method in every object that would show up in `hasattr` in addition to the boolean `make` parameter
#                 if args_dict[k]:
#                     assert qcomponent._made
#                 else:
#                     assert qcomponent._made == False
#             elif hasattr(qcomponent, k):
#                 if type(args_dict[k]) in BranchNode.BranchTypeComboBox.branch_types:
#                     qcomponent_v = getattr(qcomponent, k)
#                     param_v = args_dict[k]
#                     compare_subset(qcomponent_v, param_v)
#
#                 else:
#                     assert getattr(qcomponent, k) == args_dict[k]
#             elif hasattr(qcomponent, "_" + k):
#                 assert getattr(qcomponent, "_" + k) == args_dict[k]
#             else:
#                 raise Exception("MISSING ATTRIBUTE: ", k)
#
#
#     def compare_subset(qcomponent_v, param_v):
#         for k in param_v.keys():
#             if type(param_v[k]) in BranchNode.BranchTypeComboBox.branch_types:
#                 # Ordered Dictionaries do NOT stay ordered dictionaries in Routing - not sure why
#                 compare_subset(
#                     qcomponent_v[k],
#                     param_v[k])  #will error if k is missing in qcomponent
#             else:
#                 if isinstance(param_v[k], type(np.array([]))):
#                     assert (param_v[k] == qcomponent_v[k]
#                            ).all()  #compare each index of numpy array
#                 else:
#                     assert param_v[k] == qcomponent_v[k]
#     #