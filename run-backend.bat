@echo off
echo ================================
echo Starting Backend (FastAPI)
echo ================================

cd /d "%~dp0backend"

call venv\Scripts\activate

uvicorn app.main:app --reload

pause
