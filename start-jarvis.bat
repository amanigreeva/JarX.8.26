@echo off
title JARVIS - Offline AI Assistant
echo ============================================================
echo   JARVIS - Offline Agentic AI Assistant (Odysseus)
echo ============================================================
echo.

REM Step 1: Start Ollama (if not already running)
echo [1/3] Starting Ollama LLM Server...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo       Ollama is already running.
) else (
    start "" /B ollama serve
    echo       Ollama started.
    timeout /t 3 /nobreak >nul
)
echo.

REM Step 2: Start ChromaDB Vector Store
echo [2/3] Starting ChromaDB Vector Store on port 8100...
netstat -an | find "8100" | find "LISTENING" >NUL 2>NUL
if "%ERRORLEVEL%"=="0" (
    echo       ChromaDB is already running on port 8100.
) else (
    start "ChromaDB" /MIN venv\Scripts\chroma.exe run --host localhost --port 8100 --path data\chromadb
    echo       ChromaDB started.
    timeout /t 3 /nobreak >nul
)
echo.

REM Step 3: Start Odysseus Web UI
echo [3/3] Starting Odysseus Web UI on port 7000...
echo.
echo ============================================================
echo   All services started!
echo   Open: http://127.0.0.1:7000
echo   Username: admin / Password: admin123
echo ============================================================
echo.

powershell -ExecutionPolicy Bypass -File .\launch-windows.ps1
