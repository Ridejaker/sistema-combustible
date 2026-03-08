@echo off
title FuelMaster
cd /d "D:\PROYECTO APLICACIONES Y PAGINAS WEB\SISTEMA DE CUADROS DE CARGAS"
echo.
echo  FuelMaster - Technological Imperius
echo  Abre: http://localhost:5000
echo.
call venv\Scripts\activate.bat
python app.py
pause
