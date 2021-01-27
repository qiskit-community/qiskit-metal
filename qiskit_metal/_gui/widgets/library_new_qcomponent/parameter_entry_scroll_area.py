from PySide2.QtWidgets import (QLabel, QScrollArea, QVBoxLayout, QLabel, QWidget, QHBoxLayout, QLineEdit, QGroupBox)
from PySide2.QtWidgets import QPushButton, QApplication,  QMainWindow,  QFileSystemModel
from PySide2.QtWidgets import (QLabel, QScrollArea, QVBoxLayout, QLabel, QWidget, QHBoxLayout, QLineEdit,
                               QGroupBox)
from .parameter_entry_scroll_area_ui import Ui_ScrollArea
from PySide2.QtCore import QModelIndex, QDir
from typing import Dict
from .collapsable_widget import CollapsibleWidget
from .parameter_entry_scroll_area_ui import Ui_ScrollArea
from inspect import signature
import inspect
from collections.abc import Callable
import os
from ....designs.design_base import QDesign
class ParameterEntryScrollArea(QScrollArea,Ui_ScrollArea):

    def __init__(self,
                 QLIBRARY_FOLDERNAME: str,
                 abs_file_path: str,
                 design:QDesign,
                 parent=None,
                 *args,
                 **kwargs
                 ):
        print("initting")
        print("self type: ", str(type(self)))
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)

        print("creating Scroll")

        self.QLIBRARY_FOLDERNAME = QLIBRARY_FOLDERNAME
        self.abs_file_path = abs_file_path
        self.design = design


        self.make_button  = QPushButton("MAKE")
        self.make_button.clicked.connect(self.make_object)
        self.parameter_values = []

        self.classname, self.imported_class = self.get_class_from_abs_file_path(self.abs_file_path)
        print("classname: ", self.classname)
        self.display_class_parameter_entries(self.imported_class)
        print("displayed class parameter entries")


    # https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
    def get_class(self, import_statement):
        # parts = import_statement.split('.')
        # module = ".".join(parts[:-1])

        print("module is: ", import_statement)
        m = __import__(import_statement)
        parts = import_statement.split('.')
        for comp in parts[1:]:
            print("comp is: ", comp)
            m = getattr(m, comp)
            print("m is: ", m)

        # get classes - there is only one
        # inspect.getmembers(object[, predicate]):¶
        #   Return all the members of an object in a list of (name, value) pairs sorted by name.
        #   If the optional predicate argument—which will be called with the value object of each member—is supplied,
        #   only members for which the predicate returns a true value are included.
        members = inspect.getmembers(m, inspect.isclass)
        return members[0][0], members[0][1]

    def get_class_from_abs_file_path(self, abs_file_path):
        print("abs file path: ", abs_file_path)
        root_dir = QDir(os.getcwd())
        relative_path = root_dir.relativeFilePath(abs_file_path)  # relative path for CWD at runtime!
        print("relative path: ", relative_path)
        relative_import = relative_path.replace('/', '.').strip(".py")


        classname, imported_class = self.get_class(relative_import)
        return classname, imported_class

    def display_class_parameter_entries(self, cls: Callable):
        class_signature = signature(cls.__init__)

        for _, param in class_signature.parameters.items():
            if param.name != 'self' and param.name != 'Qdesign':
                # TODO handle *args
                # TODO handle **kwargs

                cur_type = param.annotation
                cur_name = param.name
                cur_default = param.default
                print("cur_name", cur_name)
                print("cur_type:", cur_type)

                if not param.default:
                    # TODO show mandatory via color
                    print("not default")
                # TODO fill in non-mandatory with their default values
                if cur_type is Dict:
                    print("dict")
                    cur_collapsable = CollapsibleWidget()
                    cur_collapsable_layout = QVBoxLayout()
                    cur_collapsable.setLayout(cur_collapsable_layout)


                    for i in range(2): #TODO dont hardcode 2
                        entry_widget = QWidget()
                        entry_layout = QHBoxLayout()
                        entry_widget.setLayout(entry_layout)
                        name_o = QLineEdit()
                        label = QLabel("=")
                        value_o = QLineEdit()
                        entry_layout.addWidget(name_o)
                        entry_layout.addWidget(label)
                        entry_layout.addWidget(value_o)
                        cur_collapsable_layout.addWidget(entry_widget)
                    cur_collapsable.setContentLayout(cur_collapsable_layout)


                    self.parameter_entry_vertical_layout.addWidget(cur_collapsable)
                    self.parameter_values.append((param.name, cur_type, (name_o, value_o), cur_default))
                elif cur_type is signature().empty:
                    pass
                else:
                    print("no dict")
                    cur_widget = QWidget()
                    cur_widget_hori_layout = QHBoxLayout()

                    cur_label = QLabel(cur_name)
                    cur_line_edit = QLineEdit()

                    self.parameter_values.append((param.name, cur_type, cur_line_edit, cur_default)) # C'est la vie


                    cur_widget_hori_layout.addWidget(cur_label)
                    cur_widget_hori_layout.addWidget(cur_line_edit)
                    cur_widget.setLayout(cur_widget_hori_layout)
                    self.parameter_entry_vertical_layout.addWidget(cur_widget)

                    #move to UI?
        self.parameter_entry_vertical_layout.addWidget(self.make_button)
        print("made it")




    def convert_string_to_obj(self, strvalue, ctype, default):
        if ctype is type(design):
            return self.design
        if strvalue == "":
            return default
        if ctype is Dict:
            pass
            # TODO handle dictionaries
        print("value: ", str(strvalue))
        print("valuetype: ", type(strvalue))
        print("ctype: ", ctype)
        try:
            value = ctype(strvalue)
            return value
        except:
            try:
                import json
                value = json.loads(strvalue)
                return value
            except:
                raise Exception("CANNOT USE ARGUMENTS")


    def make_object(self):
        args = []
        for ptup in self.parameter_values:
            ctype = ptup[1]
            cur_line_edit = ptup[2]
            cur_default = ptup[3]


            value = self.convert_string_to_obj(cur_line_edit.text(), ctype, cur_default)
            print("value: ", str(value))
            print("valuetype: ", type(value))
            args.append(value)

        # * operator simply unpacks the tuple (or any iterable) and passes them as the positional arguments to the function.
        self.instantiated_component = self.imported_class(*args) # TODO use try catch maybe
        self.close()

    # go through signature and get name and type
    # if dict use CollapsibleWidget with two boxes for each


    # when press make:
      #design
      #make=True  -- issues? kwarg when already

      #use param dictionary to type cast or if dict then try to json loads, if all fails
      #




