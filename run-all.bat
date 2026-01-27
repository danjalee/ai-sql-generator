@echo off
echo =========================================
echo Starting AI SQL Generator (ALL SERVICES)
echo =========================================

REM --- Start Ollama ---
echo Starting Ollama...
start "" cmd /k "ollama serve"

REM --- Start Backend ---
echo Starting Backend...
start "" cmd /k "%~dp0run-backend.bat"

REM --- Start Frontend ---
echo Starting Frontend...
start "" cmd /k "%~dp0run-frontend.bat"

echo =========================================
echo All services started!
echo =========================================
