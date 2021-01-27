import pytestqt
import pytest
import hypothesis
import pytest_bdd
import pytest_cov
import inspect

from qiskit_metal._gui.widgets.library_new_qcomponent.parameter_entry_scroll_area import ParameterEntryScrollArea
from qiskit_metal import qlibrary
from qiskit_metal.qlibrary.basic.circle_caterpillar import CircleCaterpillar
from qiskit_metal.qlibrary.connectors.cpw_hanger_t import CPWHangerT
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from addict.addict import Dict
from datetime import datetime


from PySide2.QtCore import Qt

from PySide2.QtWidgets import QPushButton

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

# these vars will be subset of what real QComponent ends with
@pytest.mark.parametrize(
     "test_name, component_file, parameters_dict",
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


def test_name_only_QComponent(qtbot, test_name, component_file, parameters_dict):
    # open ParameterEntryScrollArea w/ abs file path
    # create with different entries (parameterize testsV
    QLIBRARY_ROOT = qlibrary.__name__
    new_design = designs.DesignPlanar()

    # options=dict(connection_pads=dict(a=dict())))
    # none options
    pesa = ParameterEntryScrollArea(QLIBRARY_ROOT, component_file, new_design)
    qtbot.addWidget(pesa)
    pesa.parameter_entry_vertical_layout
    entry_count = pesa.parameter_entry_vertical_layout.count()
    for index in range(entry_count):
        cur_widget = pesa.parameter_entry_vertical_layout.itemAt(index).widget()
        if isinstance(cur_widget, pesa.EntryWidget):
            if cur_widget.arg_name in parameters_dict:
                if isinstance(cur_widget, pesa.NormalEntryWidget):
                    cur_widget.value_edit.setText(str(parameters_dict[cur_widget.arg_name]))
                elif isinstance(cur_widget, ParameterEntryScrollArea.DictionaryEntryWidget):
                    qtbot.add_widget(cur_widget)
                    create_gui_dictionary(qtbot, cur_widget.all_key_value_pairs_entry_layout,
                                           cur_widget.add_more_button, parameters_dict[cur_widget.arg_name])
    pesa.make_button.click()
    qcomponent = new_design.components[parameters_dict["name"]]

    for k,v in parameters_dict.items():
        if k == "make": #must come first because there is `make` method in every object in addition to the boolean `make` parameter
            print(k,"k is make")
            if parameters_dict[k]:
                assert qcomponent._made
            else:
                assert qcomponent._made == False
        elif hasattr(qcomponent, k):
            print("has ", k)
            if type(parameters_dict[k]) is dict:
               qcomponent_v = getattr(qcomponent, k)
               param_v = parameters_dict[k]
               compare_subset(qcomponent_v, param_v)

            else:
                assert getattr(qcomponent, k) == parameters_dict[k]
        elif hasattr(qcomponent, "_" + k):
            print("has _", k)
            assert getattr(qcomponent, "_" + k) == parameters_dict[k]
        else:
            raise Exception("MISSING ATTRIBUTE: ", k)

    del(new_design)


def compare_subset(qcomponent_v, param_v):
    for k in param_v.keys():
        if type(param_v[k]) is dict or type(param_v[k]) is Dict:
            compare_subset(qcomponent_v[k], param_v[k]) #will error if k is missing in qcomponent
        else:
            assert param_v[k] == qcomponent_v[k]

@pytest.mark.parametrize(
    "test_name, component_file, parameters_dict",
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
def test_create_dictionary(qtbot, test_name, component_file, parameters_dict): # doesn't test + button :(
    # open ParameterEntryScrollArea w/ abs file path
    # create with different entries (parameterize tests)
    QLIBRARY_ROOT = qlibrary.__name__
    new_design = designs.DesignPlanar()

    ## Create GUI input from dictionary
    pesa = ParameterEntryScrollArea(QLIBRARY_ROOT, component_file, new_design)
    qtbot.addWidget(pesa)
    entry_count = pesa.parameter_entry_vertical_layout.count()
    a_dictionary = None
    for index in range(entry_count):
        cur_widget = pesa.parameter_entry_vertical_layout.itemAt(index).widget()
        if isinstance(cur_widget, pesa.EntryWidget):
            if isinstance(cur_widget, pesa.DictionaryEntryWidget):
                a_dictionary = cur_widget
    qtbot.addWidget(a_dictionary)

    create_gui_dictionary(qtbot, a_dictionary.all_key_value_pairs_entry_layout, a_dictionary.add_more_button, parameters_dict)
    #
    #
    ## Create dictionary from GUI input
    new_dict = {}
    pesa.dictionaryentrybox_to_dictionary(a_dictionary.all_key_value_pairs_entry_layout, new_dict)
    #

    ## Compare dictionaries
    assert new_dict == parameters_dict

    pp = pprint.PrettyPrinter(indent=4)
    print("new dict: ")
    pp.pprint(new_dict)
    print("para dict:")
    pp.pprint(parameters_dict)

    del new_design

def create_gui_dictionary(qtbot, dict_box_layout, add_box_button: QPushButton, param_dict: dict):
    if param_dict == {}:
        return
    # {key: value,
    #    key: ({k2 : value}, dict/Dict)
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
        if v_type != dict and v_type != Dict:
            print("\nnewkey: ", cur_box.name_o.text())
            cur_box.value_o.setText(str(value))
            cur_box.type_name.setCurrentText(v_type.__name__)
        else:
            print("clicking nest")
            qtbot.mouseClick(cur_box.nested_dict_button, Qt.LeftButton) #should turn value_o into dictBox inside of the self.sub_entry_collapsable
            assert isinstance(cur_box.value_o, ParameterEntryScrollArea.DictionaryEntryWidget.DictionaryEntryBox)
            create_gui_dictionary(qtbot, cur_box.nested_dictionary.nested_kv_layout, cur_box.nested_dictionary.add_more_button, value)


# more button
#curbox is dbox
# for k,v in items:
    #if curBox is None:
        # call button for new box

    #if v is normal -> add normal ; curBox = None
    # else
    # nest dictionary (nest-button, nest-dbox, subdict)

# test mismatched type in dict
# test bad type in       ("dictionary_bad_type", inspect.getfile(TransmonCross), {"name": "mytransmoncross2", "Bad Type": datetime(3,3,3) }) #cannot handle types that aren't str, bool, float, or int
#
# def test_remove_button():
#     pass
#
# # test remove?
#
# def test_create_nested_dictionary():
#     pass
# #
# #
# #     #test options <= options
# #     #make
# #
# #     #see if they exist in design
# #
# #
# #     #tests:
# #     [{"name":"country"}, {"key":{"k2":"value"}}]
# #     # none options
# #     # nest dict
#
#
# # test no make input
