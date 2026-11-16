@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

%PYTHON% -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
if errorlevel 1 exit /b 1

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python -m pytest tests -q
if errorlevel 1 exit /b 1

pyinstaller --noconfirm --clean --windowed --onedir --name SapphireCalculator --collect-all PySide6 --hidden-import=requests --icon assets\sapphire-calculator.ico main.py
if errorlevel 1 exit /b 1

echo.
echo Build complete: dist\SapphireCalculator\SapphireCalculator.exe
endlocal
