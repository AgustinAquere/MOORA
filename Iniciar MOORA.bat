@echo off
rem ============================================================
rem  MOORA - doble clic para iniciar la aplicacion.
rem   1. Crea el entorno de Python (.venv) si no existe o esta danado.
rem   2. launcher.py verifica que esten instalados todos los paquetes
rem      de requirements.txt (e instala los que falten), inicia el
rem      servidor y abre el navegador.
rem ============================================================
setlocal
cd /d "%~dp0"
title MOORA - Decision multicriterio

if not exist ".venv\Scripts\python.exe" goto create
".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
if not errorlevel 1 goto run
echo El entorno de Python (.venv) esta danado: se va a crear de nuevo.
rmdir /s /q ".venv"

:create
echo ============================================================
echo  Creando el entorno de Python (.venv).
echo  La primera vez puede tardar unos minutos y requiere internet.
echo ============================================================
echo.
set "PYCMD="
where py >nul 2>nul && set "PYCMD=py -3"
if not defined PYCMD where python >nul 2>nul && set "PYCMD=python"
if not defined PYCMD goto nopython
%PYCMD% -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install --upgrade pip

:run
".venv\Scripts\python.exe" launcher.py
if errorlevel 1 pause
exit /b 0

:nopython
echo No se encontro Python en este equipo.
echo Instale Python 3.10 o superior desde https://www.python.org/downloads/
echo (marque la opcion "Add python.exe to PATH") y vuelva a abrir este archivo.
echo.
pause
exit /b 1

:fail
echo.
echo No se pudo crear el entorno de Python. Revise los mensajes de arriba.
pause
exit /b 1
