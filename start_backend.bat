@echo off
title BREAST CARE-MA Backend Server
echo Starting BREAST CARE-MA FastAPI Backend on http://localhost:8000...
cd /d %~dp0
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
