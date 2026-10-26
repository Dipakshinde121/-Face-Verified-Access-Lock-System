@echo off
REM ==============================================================================
REM run_docker.bat - Build & Run the Central Access Control Server in Docker
REM ==============================================================================

echo [1/3] Checking Docker daemon...
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [2/3] Building and starting container...
docker compose up -d --build

echo [3/3] Checking container status...
docker compose ps

echo.
echo ==============================================================================
echo Central Access Control Server is running in Docker!
echo Access Dashboard: https://127.0.0.1:8000/dashboard
echo API Documentation: https://127.0.0.1:8000/docs
echo ==============================================================================
pause
