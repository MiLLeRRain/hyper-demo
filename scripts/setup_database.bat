@echo off
REM Setup PostgreSQL database for trading bot using Docker

echo ============================================================
echo   PostgreSQL Database Setup (Docker)
echo ============================================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is installed
echo.

REM Check if container already exists
docker ps -a | findstr trading-bot-db >nul 2>nul
if %errorlevel% equ 0 (
    echo [WARNING] Container 'trading-bot-db' already exists
    echo.
    set /p RECREATE="Do you want to recreate it? (yes/no): "
    if /i not "%RECREATE%"=="yes" (
        echo.
        echo [CANCELLED] Setup cancelled
        pause
        exit /b 0
    )

    echo.
    echo Stopping and removing existing container...
    docker stop trading-bot-db >nul 2>nul
    docker rm trading-bot-db >nul 2>nul
    echo [OK] Old container removed
)

echo.
echo Creating PostgreSQL container...
echo.

docker run -d ^
  --name trading-bot-db ^
  -e POSTGRES_USER=trading_bot ^
  -e POSTGRES_PASSWORD=trading_bot_2025 ^
  -e POSTGRES_DB=trading_bot ^
  -p 5432:5432 ^
  --restart unless-stopped ^
  postgres:15

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to create Docker container
    pause
    exit /b 1
)

echo.
echo [OK] PostgreSQL container created successfully!
echo.

echo Waiting for PostgreSQL to be ready (10 seconds)...
timeout /t 10 /nobreak >nul

echo.
echo ============================================================
echo   Database Connection Info
echo ============================================================
echo.
echo Host:     localhost
echo Port:     5432
echo Database: trading_bot
echo Username: trading_bot
echo Password: trading_bot_2025
echo.

echo ============================================================
echo   Next Steps
echo ============================================================
echo.
echo 1. Update your .env file with:
echo    DB_PASSWORD=trading_bot_2025
echo.
echo 2. Run database migrations:
echo    alembic upgrade head
echo.
echo 3. Test the connection:
echo    python tests\testnet\test_database_simple.py
echo.
echo 4. Start the trading bot:
echo    python tradingbot.py start
echo.
echo ============================================================

pause
