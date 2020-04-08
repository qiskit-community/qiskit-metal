@echo on

Rem Set the Current path 
echo %~dp0
cd /d "%~dp0"   

echo "The current directory is %CD%"

call pyuic5 main_window_ui.ui -o main_window_ui.py --import-from .
call pyuic5 component_widget_ui.ui -o component_widget_ui.py --import-from .
call pyuic5 plot_window_ui.ui -o plot_window_ui.py --import-from .
call pyuic5 elements_ui.ui -o elements_ui.py --import-from .

call pyrcc5 main_window_rc.qrc -o main_window_rc_rc.py

pause >nul