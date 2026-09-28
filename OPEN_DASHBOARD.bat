@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [LOI] Chua co .venv. Hay chay START_WINDOWS.bat truoc.
  pause & exit /b 1
)
rem Bao dam .venv co du thu vien (openpyxl de xuat Excel, ...)
".venv\Scripts\python.exe" -c "import openpyxl" 2>nul || ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
".venv\Scripts\python.exe" -m streamlit run app.py
pause
