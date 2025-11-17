#!/bin/bash
# Reset PostgreSQL Database Script
# This script stops the container, removes the data volume, and restarts with fresh initialization

echo "========================================"
echo "PostgreSQL Database Reset Script"
echo "========================================"
echo ""

# Check if we're in the docker directory
if [ ! -f "docker-compose.yml" ]; then
    echo "ERROR: docker-compose.yml not found!"
    echo "Please run this script from the docker/ directory"
    exit 1
fi

echo "WARNING: This will DELETE ALL DATABASE DATA!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Step 1: Stopping containers..."
docker-compose down

echo ""
echo "Step 2: Removing data volume..."
docker volume rm docker_postgres_data 2>/dev/null || echo "Note: Volume may not exist or already removed"

echo ""
echo "Step 3: Starting PostgreSQL with fresh initialization..."
docker-compose up -d postgres

echo ""
echo "Step 4: Waiting for database to be ready..."
sleep 5

# Wait for health check
maxAttempts=30
attempt=0
while [ $attempt -lt $maxAttempts ]; do
    health=$(docker inspect --format='{{.State.Health.Status}}' trading_bot_postgres 2>/dev/null)
    if [ "$health" = "healthy" ]; then
        echo "Database is healthy!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Waiting for database... ($attempt/$maxAttempts)"
    sleep 2
done

echo ""
echo "Step 5: Viewing initialization logs..."
docker-compose logs postgres | grep -E "initialization|Created table|Database initialization"

echo ""
echo "========================================"
echo "Database reset completed!"
echo "========================================"
echo ""
echo "Verify the database:"
echo "  docker-compose exec postgres psql -U trading_bot -d trading_bot_dev -c '\dt'"
echo ""
