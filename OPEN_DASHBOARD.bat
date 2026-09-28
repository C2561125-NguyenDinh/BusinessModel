@echo off
cd /d "%~dp0"
rem Lan dau sau khi clone: tu tao .venv va cai thu vien (khong chay lai pipeline)
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if errorlevel 1 (echo [LOI] Chua cai Python 3.11/3.12 tu python.org & pause & exit /b 1)
  echo Tao moi truong .venv lan dau...
  py -3.12 -m venv ".venv" || py -3.11 -m venv ".venv"
  if not exist ".venv\Scripts\python.exe" (echo [LOI] Khong tao duoc .venv & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
rem Bao dam .venv co du thu vien (openpyxl de xuat Excel, ...)
".venv\Scripts\python.exe" -c "import openpyxl, streamlit" 2>nul || ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
".venv\Scripts\python.exe" -m streamlit run app.py
pause
