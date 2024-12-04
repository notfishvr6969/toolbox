@echo off
nuitka --onefile --standalone --windows-icon-from-ico=ICON.ico --output-dir=dist toolbox.py
pause