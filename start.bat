@echo off
REM LinguaAI Pro X — one command to set up and run. No Node.js needed.
REM Uses a SHARED penv environment one folder up (D:\pyhthon project\penv),
REM reused across all your projects.

set PENV=..\penv

if not exist "%PENV%" (
    echo Shared penv not found at %PENV% — creating it...
    python -m venv "%PENV%"
)

echo Installing/updating dependencies into shared penv...
"%PENV%\Scripts\python" -m pip install --quiet --upgrade pip
"%PENV%\Scripts\python" -m pip install --quiet -r requirements.txt

echo Starting LinguaAI Pro X — your browser will open automatically...
"%PENV%\Scripts\streamlit" run app.py