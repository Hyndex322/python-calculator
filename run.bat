@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py calculator.py
    goto :done
)

where python >nul 2>nul
if not errorlevel 1 (
    python calculator.py
    goto :done
)

echo Python was not found. Install it from https://www.python.org/downloads/
echo and make sure "Add python.exe to PATH" is checked.
pause

:done
endlocal
