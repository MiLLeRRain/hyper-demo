#!/bin/bash
# Setup PostgreSQL database for trading bot using Docker

echo "============================================================"
echo "  PostgreSQL Database Setup (Docker)"
echo "============================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed"
    echo ""
    echo "Please install Docker from:"
    echo "https://www.docker.com/products/docker-desktop/"
    echo ""
    exit 1
fi

echo "[OK] Docker is installed"
echo ""

# Check if container already exists
if docker ps -a | grep -q trading-bot-db; then
    echo "[WARNING] Container 'trading-bot-db' already exists"
    echo ""
    read -p "Do you want to recreate it? (yes/no): " RECREATE
    if [ "$RECREATE" != "yes" ]; then
        echo ""
        echo "[CANCELLED] Setup cancelled"
        exit 0
    fi

    echo ""
    echo "Stopping and removing existing container..."
    docker stop trading-bot-db > /dev/null 2>&1
    docker rm trading-bot-db > /dev/null 2>&1
    echo "[OK] Old container removed"
fi

echo ""
echo "Creating PostgreSQL container..."
echo ""

docker run -d \
  --name trading-bot-db \
  -e POSTGRES_USER=trading_bot \
  -e POSTGRES_PASSWORD=trading_bot_2025 \
  -e POSTGRES_DB=trading_bot \
  -p 5432:5432 \
  --restart unless-stopped \
  postgres:15

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to create Docker container"
    exit 1
fi

echo ""
echo "[OK] PostgreSQL container created successfully!"
echo ""

echo "Waiting for PostgreSQL to be ready (10 seconds)..."
sleep 10

echo ""
echo "============================================================"
echo "  Database Connection Info"
echo "============================================================"
echo ""
echo "Host:     localhost"
echo "Port:     5432"
echo "Database: trading_bot"
echo "Username: trading_bot"
echo "Password: trading_bot_2025"
echo ""

echo "============================================================"
echo "  Next Steps"
echo "============================================================"
echo ""
echo "1. Update your .env file with:"
echo "   DB_PASSWORD=trading_bot_2025"
echo ""
echo "2. Run database migrations:"
echo "   alembic upgrade head"
echo ""
echo "3. Test the connection:"
echo "   python tests/testnet/test_database_simple.py"
echo ""
echo "4. Start the trading bot:"
echo "   python tradingbot.py start"
echo ""
echo "============================================================"
