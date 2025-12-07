@echo on

Rem Set the Current path
echo %~dp0
cd /d "%~dp0"

echo "The current directory is %CD%"

call pyside6-uic -o main_window_ui.py --from-imports        main_window_ui.ui
call pyside6-uic -o component_widget_ui.py --from-imports   component_widget_ui.ui
call pyside6-uic -o plot_window_ui.py --from-imports        plot_window_ui.ui
call pyside6-uic -o elements_ui.py --from-imports           elements_ui.ui

call pyside6-rcc -o main_window_rc_rc.py                    main_window_rc.qrc

rem ############################################################################
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