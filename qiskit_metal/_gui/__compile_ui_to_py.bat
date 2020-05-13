@echo on

Rem Set the Current path 
echo %~dp0
cd /d "%~dp0"   

echo "The current directory is %CD%"

call pyuic5 main_window_ui.ui -o main_window_ui.py --import-from .
call pyuic5 component_widget_ui.ui -o component_widget_ui.py --import-from .
call pyuic5 plot_window_ui.ui -o plot_window_ui.py --import-from .
call pyuic5 elements_ui.ui -o elements_ui.py --import-from .
call pyuic5 edit_source_ui.ui -o edit_source_ui.py --import-from .

call pyrcc5 main_window_rc.qrc -o main_window_rc_rc.py

rem # Zlatko: 
rem # Qt Designer doesn't seem to know that in python you cant use self.raise
rem # since raise is a reserved word. 
rem # Instead, the functgion is called self.raise_
rem # Here i use sed on mac to replace it:
rem #         .raise)    --->    .raise_)
rem # for the whole file

rem TODO: THIS WILL FAIL --> Need to replace with Windows command 
sed -i '.original' 's/.raise)/.raise_)/g'  main_window_ui.py

pause >nul