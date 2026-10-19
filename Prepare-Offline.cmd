@echo off
cd /d "%~dp0"
docker compose build experience
if errorlevel 1 exit /b 1
if not exist offline mkdir offline
docker save -o offline\sathvick-experience-1.0.0-rc1.tar sathvick/openg2p-experience:1.0.0-rc1
if errorlevel 1 exit /b 1
 powershell -NoProfile -Command "$hash=(Get-FileHash -LiteralPath 'offline\sathvick-experience-1.0.0-rc1.tar' -Algorithm SHA256).Hash.ToLower(); Set-Content -LiteralPath 'offline\sathvick-experience-1.0.0-rc1.tar.sha256' -Encoding ascii -Value ($hash+'  sathvick-experience-1.0.0-rc1.tar')"
echo Copy this kit and the image TAR to the client. Do not include generated credentials or client data.
echo On the client run docker load -i offline\sathvick-experience-1.0.0-rc1.tar before Start.cmd.
pause
