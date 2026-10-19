@echo off
setlocal
cd /d "%~dp0"
where docker >nul 2>nul
if errorlevel 1 (
 echo Docker Desktop with Linux containers and Compose v2.24 or newer is required.
 pause
 exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
 echo Start Docker Desktop and retry.
 pause
 exit /b 1
)
docker image inspect sathvick/openg2p-experience:1.0.0-rc1 >nul 2>nul
if errorlevel 1 (
 if exist offline\sathvick-experience-1.0.0-rc1.tar (
  powershell -NoProfile -Command "$expected=(Get-Content -LiteralPath 'offline\sathvick-experience-1.0.0-rc1.tar.sha256').Split(' ')[0]; if ((Get-FileHash -LiteralPath 'offline\sathvick-experience-1.0.0-rc1.tar' -Algorithm SHA256).Hash -ne $expected) { exit 1 }"
  if errorlevel 1 goto failed
  docker load -i offline\sathvick-experience-1.0.0-rc1.tar
  if errorlevel 1 goto failed
 ) else (
  docker compose build experience
  if errorlevel 1 goto failed
 )
)
if not exist .env (
 docker compose run --rm --no-deps setup
 if errorlevel 1 goto failed
)
docker compose up -d --wait --wait-timeout 180 experience collector
if errorlevel 1 goto failed
echo.
echo Local entry: http://127.0.0.1:18110/experience/
echo For remote access follow docs\CLIENT-INTEGRATION.md and configure your HTTPS reverse proxy.
pause
exit /b 0
:failed
echo Deployment did not complete. Review the error above.
pause
exit /b 1
