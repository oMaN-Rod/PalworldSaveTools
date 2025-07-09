@echo off
title PalworldSaveTools Exe Builder
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r ..\requirements.txt
python build_exe.py
pause