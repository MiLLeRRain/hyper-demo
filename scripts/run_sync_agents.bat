@echo off
REM Run sync_agents_from_config.py with correct DB environment variables

setlocal

REM Set database environment variables for Docker PostgreSQL
set DB_USER=trading_bot
set DB_PASSWORD=trading_bot_2025
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=trading_bot_dev

echo ========================================
echo Sync Agents from config.yaml
echo ========================================
echo Database: %DB_NAME%
echo Host: %DB_HOST%:%DB_PORT%
echo User: %DB_USER%
echo ========================================
echo.

REM Run the script with arguments
python scripts\sync_agents_from_config.py %*

endlocal
