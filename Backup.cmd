@echo off
cd /d "%~dp0"
if not exist backups mkdir backups
docker compose run --rm --no-deps backup
pause
