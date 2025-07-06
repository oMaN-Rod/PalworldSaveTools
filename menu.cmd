@echo off
title PalworldSaveTools
mode con: cols=85 lines=47
powershell -command "& { $host.UI.RawUI.BufferSize = New-Object Management.Automation.Host.Size(85, 500) }"
python menu.py
pause