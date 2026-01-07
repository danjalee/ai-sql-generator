@echo off
start cmd /k run-backend.bat
timeout /t 3
start cmd /k run-frontend.bat