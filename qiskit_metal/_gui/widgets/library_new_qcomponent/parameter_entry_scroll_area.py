from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import (QScrollArea, QVBoxLayout, QLabel, QWidget, QHBoxLayout, QLineEdit, QLayout, QComboBox)
from PySide2.QtCore import Qt
from PySide2.QtCore import QDir
from addict.addict import Dict
from .collapsable_widget import CollapsibleWidget
from .parameter_entry_scroll_area_ui import Ui_ScrollArea
from inspect import signature
import inspect
from collections.abc import Callable
import os
from ....designs.design_base import QDesign
import importlib
import builtins

from typing import Dict as typeDict

class ParameterEntryScrollArea(QScrollArea,Ui_ScrollArea):
    def __init__(self,
                 QLIBRARY_FOLDERNAME: str,
                 abs_file_path: str,
                 design:QDesign,
                 parent=None,
                 *args,
                 **kwargs
                 ):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.setWidgetResizable(True)
        self.setAttribute(Qt.WA_DeleteOnClose) # delete this ParameterEntryScrollArea when it closes

        self.QLIBRARY_FOLDERNAME = QLIBRARY_FOLDERNAME
        self.abs_file_path = abs_file_path
        self.design = design

        self.parameter_values = []

        self.imported_class = self.get_class_from_abs_file_path(self.abs_file_path)
        print("import_class name:", self.imported_class.__name__)
        print("import_class:", self.imported_class)

        self.display_class_parameter_entries(self.imported_class)

    ## Parameter-Entry Qt Display Custom Classes

    class EntryWidget(QWidget):
        def __init__(self, parent_layout):
            super().__init__()
            self.parent_layout = parent_layout
            self.parent_layout.addWidget(self)

    class NormalEntryWidget(EntryWidget):
        def __init__(self, parent_layout: QLayout,arg_name:str, arg_type, arg_default):
            super().__init__(parent_layout) # add self to parent layout
            print("initting NormalEntryWidget")
            self.arg_name = arg_name
            self.arg_type = arg_type
            self.arg_default  = arg_default

            self.entry_widget_hori_layout = QHBoxLayout()
            self.setLayout(self.entry_widget_hori_layout)

            self.name_label = QLabel(arg_name)
            self.entry_widget_hori_layout.addWidget(self.name_label)

            self.value_edit = QLineEdit()
            self.entry_widget_hori_layout.addWidget(self.value_edit)

    class DictionaryEntryWidget(EntryWidget):
        def __init__(self,  parent_layout, arg_name,  arg_type, arg_default):
            #TODO arg name can be None thus QLinedEdit
            super().__init__(parent_layout)
            print("initting dictionary entry widget")
            self.arg_type = arg_type
            self.arg_name = arg_name
            self.arg_default = arg_default

            self.parent_layout.setStretchFactor(self,4)

            self.entry_layout = QHBoxLayout()
            self.setLayout(self.entry_layout)

            self.name_label = QLabel(self.arg_name)
            self.entry_layout.addWidget(self.name_label)

            self.entry_collapsable = CollapsibleWidget()
            self.entry_layout.addWidget(self.entry_collapsable)

            self.entry_collapsable_content_widget = QWidget()
            self.entry_collapsable.setContent(self.entry_collapsable_content_widget)

            self.entry_collapsable_layout = QVBoxLayout()
            self.entry_collapsable_content_widget.setLayout(self.entry_collapsable_layout)

            self.collapsable_label = QLabel("Please refer to docs to see what key, value pair options are available. "
                                       "\nNo need to write the ' nor \", your entry will automatically be converted to a string.\n"
                                       "Do not forget to include dimensions when relevent. Key types are always strings")
            self.entry_collapsable_layout.addWidget(self.collapsable_label)

            self.all_key_value_pairs_entry_widget = QWidget()
            self.entry_collapsable_layout.addWidget(self.all_key_value_pairs_entry_widget)

            self.all_key_value_pairs_entry_layout = QVBoxLayout()
            self.all_key_value_pairs_entry_widget.setLayout(self.all_key_value_pairs_entry_layout)

            self.add_more_button = QPushButton("+")
            self.all_key_value_pairs_entry_layout.addWidget(self.add_more_button)

            # "PySide2 handles connections differently than PyQt5 so use QPushButton.pressed to emit signal without args"
            self.add_more_button.pressed.connect(
                lambda cur_layout=self.all_key_value_pairs_entry_layout: self.add_key_value_entry(cur_layout)
            )

            self.add_key_value_entry(self.all_key_value_pairs_entry_layout)


            print("entry_collapsable_layout: ", self.entry_collapsable_layout)

        def add_key_value_entry(self, cur_all_key_value_pairs_entry_layout):
            print("cur_collapsable_layout: ", cur_all_key_value_pairs_entry_layout)
            return self.DictionaryEntryBox(cur_all_key_value_pairs_entry_layout)

        class DictionaryEntryBox(QWidget):
            def __init__(self, cur_all_key_value_pairs_entry_layout, parent=None):
                super().__init__(parent)
                cur_all_key_value_pairs_entry_layout.addWidget(self)
                self.nested_dictionary = None
                print("initting DictionaryEntryBox")
                self.key_value_entry_layout = QHBoxLayout()
                self.setLayout(self.key_value_entry_layout) #add self to parent layout's parent widget
                self.key_name = QLabel("Key:")
                self.name_o = QLineEdit()
                self.label = QLabel(":")
                self.value_name = QLabel("Value:")
                self.value_o = QLineEdit() # in event of nesting, self.value_o will then point to sub DictionaryEntryBox
                print("value_o run")
                self.type_name = self.TypeComboBox()
                self.remove_button = QPushButton("REMOVE")
                self.nested_dict_button = QPushButton("nest")
                self.key_value_entry_layout.addWidget(self.key_name)
                self.key_value_entry_layout.addWidget(self.name_o)
                self.key_value_entry_layout.addWidget(self.label)
                self.key_value_entry_layout.addWidget(self.value_name)
                self.key_value_entry_layout.addWidget(self.value_o)
                print("value_o added")
                self.key_value_entry_layout.setStretchFactor(self.value_o, 6) # 4x as large as smallest widget in layout imo
                self.key_value_entry_layout.addWidget(self.type_name)
                self.key_value_entry_layout.addWidget(self.remove_button)
                self.key_value_entry_layout.addWidget(self.nested_dict_button)
                print("box parts added")
                self.remove_button.pressed.connect(
                    lambda w=self, ll=cur_all_key_value_pairs_entry_layout: self.deleteWidget(w, ll)
                )
                print("remove lambda added")
                self.nested_dict_button.pressed.connect(
                    self.nest_dictionary
                )
                print("setup nested button")

            class TypeComboBox(QComboBox):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.addItem("str")
                    self.addItem("float")
                    self.addItem("int")
                    self.addItem("bool")

                def getType(self):
                    print("type current txt: ", self.currentText())
                    print("type builtins: ", type(builtins))
                    print("builtins",builtins)

                    return getattr(builtins, self.currentText())

            class NestedDictionary(CollapsibleWidget):
                def __init__(self, title, parent):
                    super().__init__(parent=parent, title=title)
                    # self.entry_collapsable replaces old value at end of NestedDictionary init
                    print("nesting")

                    self.entry_content = QWidget(self)  # DictionaryEntryBox is parent
                    self.setContent(self.entry_content)

                    self.nested_kv_layout = QVBoxLayout()
                    self.entry_content.setLayout(self.nested_kv_layout)

                    self.add_more_button = QPushButton("+")
                    self.nested_kv_layout.addWidget(self.add_more_button)

                    self.add_more_button.pressed.connect(
                        lambda cur_layout=self.nested_kv_layout: parent.__class__(cur_layout)
                    )

                    # replace parent's dictionary value QLineEdit with another DictionaryBoxEntry
                    parent.key_value_entry_layout.removeWidget(parent.value_name)
                    parent.value_name.deleteLater()

                    parent.key_value_entry_layout.replaceWidget(parent.value_o, self)
                    parent.value_o.deleteLater()
                    parent.value_o = parent.__class__(
                        self.nested_kv_layout)  # new value_o is a DEB containing all debs

            def nest_dictionary(self):
                self.nested_dictionary = self.NestedDictionary("nested dictionary", self)
                print("Self is: ", self)
                print("self.nd: ", self.nested_dictionary)


            def deleteWidget(self, widg, lay):
                lay.removeWidget(widg)
                widg.deleteLater()

    ## Parameter-Entry Qt Methods

    def display_class_parameter_entries(self, cls: Callable):
        class_signature = signature(cls.__init__)

        for _, param in class_signature.parameters.items():
            if param.name != 'self' and param.name != 'design':
                # TODO handle *args
                # TODO handle **kwargs
                entry_type = param.annotation
                cur_name = param.name
                cur_default = param.default
                print("cur_name", cur_name)
                print("entry_type:", entry_type)

                if not param.default:
                    # TODO show mandatory via color
                    # TODO fill in non-mandatory with their default values
                    if entry_type is class_signature.empty:
                        print("some error because we need signature if mandatory")

                if entry_type is type({}) or entry_type is Dict:
                    self.DictionaryEntryWidget(self.parameter_entry_vertical_layout, cur_name, entry_type, cur_default)

                else:
                    self.NormalEntryWidget(self.parameter_entry_vertical_layout, cur_name, entry_type, cur_default)

        self.make_button  = QPushButton("MAKE")
        self.make_button.clicked.connect(self.make_object)
        self.parameter_entry_vertical_layout.addWidget(self.make_button)
        print("made it")

    def deleteWidget(self, widg, lay):
        lay.removeWidget(widg)
        widg.deleteLater()


    ## Reading User Input and Instantiating Component Methods

    # https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
    def get_class(self, import_statement):
        mymodule = importlib.import_module(import_statement)
        members = inspect.getmembers(mymodule, inspect.isclass)
        class_owner = import_statement.split('.')[-1]

        for memtup in members:
            if  str(memtup[1].__module__).endswith(class_owner):
                return memtup[1]

    def get_class_from_abs_file_path(self, abs_file_path):
        root_dir = QDir(os.getcwd())
        #relative_path = root_dir.relativeFilePath(abs_file_path)  # relative path for CWD at runtime!
        #relative_import = relative_path.replace('/', '.')[:-len('.py')] if relative_path.endswith('.py') else relative_path.replace('/', '.')
        qis_abs_path = abs_file_path[abs_file_path.index(__name__.split('.')[0]):]
        qis_mod_path = qis_abs_path.replace('/', '.')[:-len('.py')]
        imported_class = self.get_class(qis_mod_path)
        return imported_class

    def convert_string_to_obj(self, entry_value, ctype, default):
        print("value: ", str(entry_value))
        print("valuetype: ", type(entry_value))
        print("ctype: ", ctype)
        if entry_value == "" or entry_value == [] :
            return default
        if ctype is Dict or ctype is type({}):
            print("dictionarying")
            my_dictionary = {}
            typ_d = {"str":str, "int":int }
            for entries in entry_value:
                print("entry_value: ", entry_value)
                #these are each QLineEdits
                k = entries[0].text()
                v = entries[1].text()
                t = typ_d[entries[2].text()]
                print("t: ", t)
                my_dictionary[k] = t(v)
                print("current dictionary: ", my_dictionary)
            return my_dictionary

            # TODO handle nested dictionaries

        try:
            value = ctype(entry_value.text())
            return value
        except:
            try:
                import json
                value = json.loads(entry_value)
                return value
            except:
                raise Exception("CANNOT USE ARGUMENTS")

    def dictionaryentrybox_to_dictionary(self, parent_layout, kv_dict):
        #get all Debs from layout and add to kv_dict
        kv_count = parent_layout.count()
        print("kv_count: ", kv_count)
        for index in range(kv_count):
            cur_widget = parent_layout.itemAt(index).widget() # at least one entry should be + button
            if isinstance(cur_widget, self.DictionaryEntryWidget.DictionaryEntryBox):
                #get keyname:
                keyname = cur_widget.name_o.text()
                print("\npeda key: ", keyname)
                if keyname != "":
                    print("keyname: ", keyname)
                    #subdictionaries will always be of type dict not of type addict.Dict
                    value_widget = cur_widget.value_o
                    if isinstance(value_widget, self.DictionaryEntryWidget.DictionaryEntryBox):
                        value = {}
                        self.dictionaryentrybox_to_dictionary(cur_widget.nested_dictionary.nested_kv_layout, value)
                    else:
                        print("value_widget is: ", value_widget)
                        #DictionaryBoxEntries must be of a __builtin__ type
                        strvalue = value_widget.text()
                        if strvalue == "":
                            value = None # todo perhaps do "" and 0 instead
                        else:
                            cur_type = cur_widget.type_name.getType()
                            if cur_type == bool:
                                if strvalue.lower() in "true":
                                    value = True
                                else:
                                    value = False
                            else:
                                value = cur_type(strvalue)
                    kv_dict[keyname] =  value

        print("kv_dict is: ", kv_dict)

    def argifyEntry(self, entry, argdict):
        if isinstance(entry, self.NormalEntryWidget):
            print("Normal")
            strvalue = entry.value_edit.text()
            print("ed.txt()", strvalue)
            if  strvalue == "":
                print("default arg bc ", strvalue)
                print("default arg: ", entry.arg_default)
                value = entry.arg_default
            else:
                if entry.arg_type == bool:
                    if strvalue.lower() in "true":
                        value = True
                    else:
                        value = False
                else:
                    value = entry.arg_type(strvalue)
            print("final value: ", value)
            argdict[entry.arg_name] = value
            print("entry.arg_name: ", entry.arg_name)
            print("entry.arg_name type: ", type(entry.arg_name))


        elif isinstance(entry, self.DictionaryEntryWidget):
            deb_dict = {}
            self.dictionaryentrybox_to_dictionary(entry.all_key_value_pairs_entry_layout, deb_dict)
            argdict[entry.arg_name] = entry.arg_type(deb_dict)



    def make_object(self):
        print("mak obj")
        try:
             entry_count = self.parameter_entry_vertical_layout.count()
             kwargs = {}
             for index in range(entry_count):
                 cur_widget = self.parameter_entry_vertical_layout.itemAt(index).widget()
                 if isinstance(cur_widget, self.EntryWidget):
                     print("will arg: ", cur_widget.arg_name)
                     self.argifyEntry(cur_widget, kwargs)


             #instantiate QComponent (QRoute, Qbit, etc.)
             # * operator simply unpacks the tuple (or any iterable) and passes them as the positional arguments to the function.
             print("all args added to kwargs", kwargs)
             print("imported class", self.imported_class)
             im = self.imported_class(self.design, **kwargs) # TODO use try catch maybe
             print("imported class: ", im)
             self.close()
        except Exception as e:
            print("Make Object Failed: ", e)

    # when press make:
      #design
      #make=True  -- issues? kwarg when already

      #use param dictionary to type cast or if dict then try to json loads, if all fails
      #




