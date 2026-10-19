@echo off
cd /d "%~dp0"
docker compose ps
docker compose exec -T experience python tools/healthcheck.py
docker compose exec -T collector python collector.py
pause
