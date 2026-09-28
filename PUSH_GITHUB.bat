@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Day project len GitHub
echo ============================================================
echo  DAY PROJECT FAVORITA LEN GITHUB
echo ============================================================

where git >nul 2>nul
if errorlevel 1 (
  echo [LOI] Chua cai Git. Tai tai https://git-scm.com/download/win roi chay lai file nay.
  pause & exit /b 1
)

rem --- Thong tin nguoi commit (chi hoi lan dau) ---
for /f "delims=" %%A in ('git config --global user.name 2^>nul') do set GUSER=%%A
if not defined GUSER (
  set /p GUSER=Nhap ten hien thi tren GitHub: 
  git config --global user.name "!GUSER!"
)
for /f "delims=" %%A in ('git config --global user.email 2^>nul') do set GMAIL=%%A
if not defined GMAIL (
  set /p GMAIL=Nhap email tai khoan GitHub: 
  git config --global user.email "!GMAIL!"
)

rem --- Khoi tao repository neu chua co ---
git config --global --add safe.directory "%CD:\=/%" >nul 2>nul
if not exist ".git" (
  echo Khoi tao repository moi...
  git init -q
  git symbolic-ref HEAD refs/heads/main
)

rem --- Gan dia chi repository tren GitHub ---
set REPO=https://github.com/C2561125-NguyenDinh/BusinessModel.git
git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin "!REPO!"
) else (
  git remote set-url origin "!REPO!"
)
echo Repository: !REPO!

rem --- Chan file lon hon 95 MB (GitHub gioi han 100 MB/file) ---
git add -A
set BIG=
for /f "delims=" %%F in ('git diff --cached --name-only') do (
  if exist "%%F" for %%S in ("%%F") do if %%~zS GTR 99614720 (
    echo [CANH BAO] Bo qua file lon: %%F
    git reset -q -- "%%F"
    set BIG=1
  )
)
if defined BIG echo Hay them cac file tren vao .gitignore neu khong can dua len.

rem --- Commit ---
set MSG=
set /p MSG=Noi dung commit (Enter = "Cap nhat project"): 
if "!MSG!"=="" set MSG=Cap nhat project
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "!MSG!"
) else (
  echo Khong co thay doi moi de commit.
)

rem --- Day len GitHub ---
echo.
echo Dang day len GitHub (lan dau se mo cua so dang nhap GitHub)...
git branch -M main >nul 2>nul
git push -u origin main
if errorlevel 1 (
  echo.
  echo [LOI] Day len that bai. Kiem tra:
  echo   - Dia chi repository dung chua:  git remote -v
  echo   - Repository tren GitHub co dang TRONG khong (neu da co README, chay: git pull origin main --allow-unrelated-histories^)
  echo   - Da dang nhap GitHub trong cua so hien ra chua
  pause & exit /b 1
)
echo.
echo ============================================================
echo  HOAN TAT. Mo repository tren github.com de kiem tra.
echo ============================================================
pause
