@echo off
setlocal

cd /d "%~dp0"

set PYTHON=%%~dp0python.exe
set SCRIPT=%%~dp0run_script.py

if not exist "%%SCRIPT%%" (
    echo File %%SCRIPT%% not found.
    exit /b 1
)

%%PYTHON%% %%SCRIPT%% %*

endlocal
