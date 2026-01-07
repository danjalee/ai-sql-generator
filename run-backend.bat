@echo off
echo ================================
echo Starting SQL Agent Backend
echo ================================

cd backend

REM Activate virtual environment
call venv\Scripts\activate

REM Run FastAPI with auto reload
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause