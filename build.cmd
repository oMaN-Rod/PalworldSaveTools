@echo off
title PalworldSaveTools Exe Builder
echo ========================================
echo PalworldSaveTools Exe Builder
echo ========================================
if exist venv (
    echo venv found, skipping creation and install...
) else (
    echo Now creating venv...
    python -m venv venv
    echo Now installing the requirements to venv...
    venv\Scripts\pip.exe install -r requirements.txt
)
echo Now building the .exe...
venv\Scripts\python.exe build.py
echo Exe building completed!
pause