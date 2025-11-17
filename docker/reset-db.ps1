# Reset PostgreSQL Database Script
# This script stops the container, removes the data volume, and restarts with fresh initialization

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL Database Reset Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the docker directory
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "ERROR: docker-compose.yml not found!" -ForegroundColor Red
    Write-Host "Please run this script from the docker/ directory" -ForegroundColor Red
    exit 1
}

Write-Host "WARNING: This will DELETE ALL DATABASE DATA!" -ForegroundColor Yellow
Write-Host ""
$confirmation = Read-Host "Are you sure you want to continue? (yes/no)"

if ($confirmation -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Step 1: Stopping containers..." -ForegroundColor Green
docker-compose down

Write-Host ""
Write-Host "Step 2: Removing data volume..." -ForegroundColor Green
docker volume rm docker_postgres_data 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Note: Volume may not exist or already removed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 3: Starting PostgreSQL with fresh initialization..." -ForegroundColor Green
docker-compose up -d postgres

Write-Host ""
Write-Host "Step 4: Waiting for database to be ready..." -ForegroundColor Green
Start-Sleep -Seconds 5

# Wait for health check
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    $health = docker inspect --format='{{.State.Health.Status}}' trading_bot_postgres 2>$null
    if ($health -eq "healthy") {
        Write-Host "Database is healthy!" -ForegroundColor Green
        break
    }
    $attempt++
    Write-Host "Waiting for database... ($attempt/$maxAttempts)" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "Step 5: Viewing initialization logs..." -ForegroundColor Green
docker-compose logs postgres | Select-String "initialization|Created table|Database initialization"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Database reset completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verify the database:" -ForegroundColor Cyan
Write-Host "  docker-compose exec postgres psql -U trading_bot -d trading_bot_dev -c '\dt'" -ForegroundColor White
Write-Host ""
