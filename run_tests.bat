@echo off
title BREAST CARE-MA Test Suite
echo Running BREAST CARE-MA Verification Suite...
cd /d %~dp0
python -u -m backend.test_pipeline
pause
