@echo off
nuitka --onefile --standalone --enable-plugin=pyqt5 --windows-icon-from-ico=ICON.ico --windows-console-mode=disable --output-dir=dist toolbox.py
pause