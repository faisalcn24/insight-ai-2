@echo off
echo Starting INSIGHT.AI...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Ollama if not already running
start "" ollama serve

REM Wait a moment for Ollama to start
timeout /t 3 /nobreak >nul

REM Launch the Streamlit app
streamlit run functions/dashboard.py

pause