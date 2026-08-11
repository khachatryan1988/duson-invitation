@echo off
echo Starting DUSON Invitation...
docker compose up -d --build
echo.
echo Website: http://localhost:8000
echo Admin:   http://localhost:8000/admin
echo.
docker compose ps
pause
