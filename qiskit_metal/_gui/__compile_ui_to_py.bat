Rem Set the CUrrent path 

echo %~dp0
cd /d "%~dp0"   

echo The current directory is %CD%

pyuic5 main_window_ui.ui -o main_window_ui.py 
pyrcc5 main_window_rc.qrc -o main_window_rc.py

pause >nul