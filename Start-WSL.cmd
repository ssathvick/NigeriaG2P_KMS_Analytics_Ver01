@echo off
setlocal
cd /d "%~dp0"
wsl.exe -d Ubuntu-22.04 -u root -- docker info >nul 2>nul
if errorlevel 1 (
 echo Docker Engine must be running inside the Ubuntu-22.04 WSL2 distribution.
 echo See docs\CLIENT-INTEGRATION.md. Docker Desktop is not needed for this option.
 pause
 exit /b 1
)
wsl.exe -d Ubuntu-22.04 -u root -- bash ./install.sh
if errorlevel 1 (
 echo Deployment did not complete. Review the error above.
 pause
 exit /b 1
)
pause
