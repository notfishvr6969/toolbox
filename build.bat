@echo off
nuitka --onefile --standalone --windows-icon-from-ico=ICON.ico --windows-console-mode=disable --output-dir=dist toolbox.py
pause