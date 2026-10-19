@echo off
cd /d "%~dp0"
wsl.exe -d Ubuntu-22.04 -u root -- bash ./backup.sh
pause
