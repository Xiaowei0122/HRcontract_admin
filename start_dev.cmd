@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title HRcontract Dev Startup

echo.
echo ========================================================
echo    HRcontract - One-Click Dev Services Startup
echo ========================================================
echo.
echo    Frontend : http://localhost:5173
echo    Backend  : http://localhost:9080/docs
echo    MongoDB  : 192.168.1.111:32768
echo    MinIO    : 192.168.1.111:9000
echo.
echo ========================================================
echo.

REM ============================================================
REM  1.  Check / Start MongoDB
REM ============================================================
echo [1/4] Checking MongoDB ...

REM Quick port check using a simple PowerShell one-liner
powershell -Command "if ((Test-NetConnection 192.168.1.111 -Port 32768).TcpTestSucceeded) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo        [OK] MongoDB is reachable
) else (
    echo        [WARN] MongoDB not reachable, trying Docker...
    docker start mongo-1 >nul 2>&1
    if %errorlevel% neq 0 (
        echo        [WARN] No mongo-1 container, running docker compose...
        docker compose up -d mongo-1 >nul 2>&1
    )
    echo        Waiting 5 seconds for MongoDB to start...
    timeout /t 5 /nobreak >nul
)
echo.

REM ============================================================
REM  2.  Check / Start MinIO
REM ============================================================
echo [2/4] Checking MinIO ...

powershell -Command "if ((Test-NetConnection 192.168.1.111 -Port 9000).TcpTestSucceeded) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo        [OK] MinIO is reachable
) else (
    echo        [WARN] MinIO not reachable, trying Docker...
    docker start minio-1 >nul 2>&1
    if %errorlevel% neq 0 (
        echo        [WARN] No minio-1 container, running docker compose...
        docker compose up -d minio-1 >nul 2>&1
    )
    echo        Waiting 5 seconds for MinIO to start...
    timeout /t 5 /nobreak >nul
)
echo.

REM ============================================================
REM  3.  Start Backend (FastAPI on port 9080)
REM ============================================================
echo [3/4] Starting Backend  -^> http://localhost:9080
if not exist "src\api\main.py" (
    echo        [ERROR] src\api\main.py not found!
    pause
    exit /b 1
)
start "HR-Backend-9080" cmd /k "cd /d "%~dp0src\api" && echo HR Backend starting... && python main.py"
echo        [OK] Backend launched in a new window
echo.

REM ============================================================
REM  3.  Start Frontend (Vite on port 5173)
REM ============================================================
echo [4/4] Starting Frontend -^> http://localhost:5173
if not exist "package.json" (
    echo        [ERROR] package.json not found!
    pause
    exit /b 1
)
start "HR-Frontend-5173" cmd /k "cd /d "%~dp0" && echo HR Frontend starting... && npm run dev"
echo        [OK] Frontend launched in a new window
echo.

REM ============================================================
REM  Open browser
REM ============================================================
echo Waiting 6 seconds for services to compile...
timeout /t 6 /nobreak >nul
start http://localhost:5173

echo.
echo ========================================================
echo    All services started!
echo.
echo    Frontend : http://localhost:5173
echo    Backend  : http://localhost:9080/docs
echo.
echo    Close each CMD window to stop its service.
echo ========================================================
echo.

pause
