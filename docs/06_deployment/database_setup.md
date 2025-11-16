# PostgreSQL 16 Docker Setup Guide

Complete guide to setting up PostgreSQL 16 using Docker for the Trading Bot.

---

## Quick Start (Recommended)

### Prerequisites

- Docker installed ([Get Docker](https://www.docker.com/get-started))
- Docker Compose installed (included with Docker Desktop)

> **Note**: All Docker files are located in the `docker/` directory. You need to run commands from that directory.

### 1. Start PostgreSQL with Docker Compose

```bash
# Navigate to docker directory
cd docker

# Start PostgreSQL 16 container
docker-compose up -d postgres

# Check container status
docker-compose ps

# View logs
docker-compose logs -f postgres
```

Expected output:
```
✅ Container trading_bot_postgres  Started
✅ PostgreSQL 16 is ready to accept connections
✅ Database initialization completed!
```

### 2. Verify Database

```bash
# Connect to database
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev

# In psql prompt, list tables:
\dt

# Should show:
#  trading_agents
#  agent_decisions
#  agent_trades
#  agent_performance
#  bot_state

# Exit psql
\q
```

### 3. Configure Application

Update `.env` file:

```bash
# Database Configuration (Docker)
DB_USER=trading_bot
DB_PASSWORD=trading_bot_2025
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_bot_dev
```

### 4. Test Connection

```bash
# Run integration tests
python run_db_tests.py

# Should see:
# ============================= 22 passed in 0.84s ==============================
```

That's it! Your PostgreSQL 16 database is ready.

---

## Docker Compose Configuration

### File: `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: trading_bot_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: trading_bot_dev
      POSTGRES_USER: trading_bot
      POSTGRES_PASSWORD: trading_bot_2025
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trading_bot -d trading_bot_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Key Features

- **PostgreSQL 16 Alpine**: Lightweight, secure, latest version
- **Auto-restart**: Container restarts unless manually stopped
- **Persistent data**: Data survives container restarts
- **Health checks**: Monitors database availability
- **Auto-initialization**: Runs `init-db.sql` on first start

---

## Docker Commands Reference

### Container Management

All commands must be run from the `docker/` directory:

```bash
cd docker

# Start database
docker-compose up -d postgres

# Stop database
docker-compose stop postgres

# Restart database
docker-compose restart postgres

# Stop and remove container (data persists)
docker-compose down

# Stop and remove container + volumes (⚠️ DELETES ALL DATA)
docker-compose down -v
```

### Logs and Monitoring

```bash
# View logs
docker-compose logs postgres

# Follow logs (Ctrl+C to exit)
docker-compose logs -f postgres

# View last 100 lines
docker-compose logs --tail=100 postgres

# Check container status
docker-compose ps

# Check resource usage
docker stats trading_bot_postgres
```

### Database Access

```bash
# Connect to psql
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev

# Run SQL file
docker-compose exec -T postgres psql -U trading_bot -d trading_bot_dev < backup.sql

# Dump database
docker-compose exec -T postgres pg_dump -U trading_bot trading_bot_dev > backup.sql
```

---

## Database Initialization

### Automatic Initialization

The database is automatically initialized with:

1. **Schema creation**: All 5 tables with indexes
2. **Sample data**: 2 sample agents
3. **Bot state**: Initial state entry

This happens automatically on first container start via `/docker/init-db.sql`.

### Manual Re-initialization

If you need to reset the database:

```bash
# Stop and remove container + volumes (⚠️ DELETES ALL DATA)
docker-compose down -v

# Start again (will re-run init script)
docker-compose up -d postgres
```

### Custom Initialization

Edit `docker/init-db.sql` to customize:
- Table structure
- Initial data
- Extensions
- Users/permissions

---

## Optional: pgAdmin (Database Management UI)

### Start pgAdmin

```bash
# Start pgAdmin alongside PostgreSQL
docker-compose --profile tools up -d

# Access pgAdmin at: http://localhost:5050
# Email: admin@tradingbot.local
# Password: admin123
```

### Connect to Database in pgAdmin

1. Open http://localhost:5050
2. Login with credentials above
3. Add New Server:
   - **Name**: Trading Bot DB
   - **Host**: postgres (container name)
   - **Port**: 5432
   - **Database**: trading_bot_dev
   - **Username**: trading_bot
   - **Password**: trading_bot_2025

---

## Production Configuration

### 1. Change Default Password

Edit `docker/docker-compose.yml`:

```yaml
environment:
  POSTGRES_PASSWORD: YOUR_STRONG_PASSWORD_HERE
```

Update `.env`:

```bash
DB_PASSWORD=YOUR_STRONG_PASSWORD_HERE
```

Generate strong password:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Use Docker Secrets (Recommended)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    secrets:
      - db_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_DB: trading_bot_prod
      POSTGRES_USER: trading_bot

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### 3. Enable SSL/TLS

Add to `docker/docker-compose.yml`:

```yaml
volumes:
  - ./docker/certs:/var/lib/postgresql/certs:ro
command: >
  -c ssl=on
  -c ssl_cert_file=/var/lib/postgresql/certs/server.crt
  -c ssl_key_file=/var/lib/postgresql/certs/server.key
```

### 4. Configure Connection Pooling

Install PgBouncer:

```yaml
services:
  pgbouncer:
    image: pgbouncer/pgbouncer
    environment:
      DATABASES_HOST: postgres
      DATABASES_PORT: 5432
      DATABASES_DBNAME: trading_bot_dev
    ports:
      - "6432:6432"
```

Update application to connect to `localhost:6432` instead of `5432`.

---

## Backup and Restore

### Automated Backups

Create `docker/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/trading_bot_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U trading_bot trading_bot_dev > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

Run daily:
```bash
chmod +x docker/backup.sh
# Add to cron: 0 2 * * * /path/to/docker/backup.sh
```

### Manual Backup

```bash
# Create backup
docker-compose exec -T postgres pg_dump -U trading_bot trading_bot_dev > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T postgres psql -U trading_bot -d trading_bot_dev < backup_20251116.sql
```

### Copy Backup from Container

```bash
# Backup inside container
docker-compose exec postgres pg_dump -U trading_bot trading_bot_dev > /tmp/backup.sql

# Copy to host
docker cp trading_bot_postgres:/tmp/backup.sql ./backup.sql
```

---

## Monitoring and Maintenance

### Check Database Size

```bash
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev -c "
SELECT pg_size_pretty(pg_database_size('trading_bot_dev'));"
```

### Check Table Sizes

```bash
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Check Active Connections

```bash
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'trading_bot_dev';"
```

### Vacuum Database

```bash
# Analyze and vacuum
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev -c "VACUUM ANALYZE;"

# Full vacuum (requires more space)
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev -c "VACUUM FULL;"
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs postgres

# Check if port 5432 is already in use
netstat -an | findstr 5432  # Windows
lsof -i :5432               # Linux/Mac

# If port is in use, change in docker-compose.yml:
ports:
  - "5433:5432"  # Use 5433 on host instead
```

### Connection Refused

```bash
# Wait for health check to pass
docker-compose ps

# Should show:
# STATUS: Up (healthy)

# If unhealthy, check logs:
docker-compose logs postgres
```

### Permission Denied

```bash
# On Linux, fix volume permissions
sudo chown -R 999:999 ./postgres_data

# Or use named volume (recommended):
# Already configured in docker-compose.yml
```

### Data Corruption

```bash
# Stop container
docker-compose stop postgres

# Remove volume (⚠️ DELETES ALL DATA)
docker volume rm hyper-demo_postgres_data

# Start fresh
docker-compose up -d postgres
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up unused images/volumes
docker system prune -a

# Remove old backups
find ./backups -name "*.sql.gz" -mtime +30 -delete
```

---

## Migration from Local PostgreSQL

### Export from Local PostgreSQL

```bash
# Dump local database
pg_dump -U postgres trading_bot_dev > local_backup.sql
```

### Import to Docker PostgreSQL

```bash
# Start Docker database
docker-compose up -d postgres

# Wait for health check
sleep 10

# Import data
docker-compose exec -T postgres psql -U trading_bot -d trading_bot_dev < local_backup.sql
```

---

## Environment-Specific Configuration

### Development

```yaml
# docker-compose.yml (already configured)
environment:
  POSTGRES_DB: trading_bot_dev
  POSTGRES_USER: trading_bot
  POSTGRES_PASSWORD: trading_bot_2025
```

### Testing

```yaml
# docker-compose.test.yml
environment:
  POSTGRES_DB: trading_bot_test
  POSTGRES_USER: trading_bot_test
  POSTGRES_PASSWORD: test_password
```

Run tests:
```bash
docker-compose -f docker-compose.test.yml up -d
pytest tests/
docker-compose -f docker-compose.test.yml down -v
```

### Production

```yaml
# docker-compose.prod.yml
environment:
  POSTGRES_DB: trading_bot_prod
  POSTGRES_USER: trading_bot_prod
secrets:
  - db_password
```

---

## Summary

### Required Steps

1. ✅ Install Docker and Docker Compose
2. ✅ Run `docker-compose up -d postgres`
3. ✅ Verify with `docker-compose exec postgres psql -U trading_bot -d trading_bot_dev`
4. ✅ Update `.env` with database credentials
5. ✅ Run `python run_db_tests.py` to verify

### Optional Steps

- Set up pgAdmin for GUI management
- Configure automated backups
- Enable SSL/TLS for production
- Set up monitoring and alerts

### Advantages of Docker Setup

- ✅ **Easy setup**: One command to start
- ✅ **Consistent**: Same environment everywhere
- ✅ **Isolated**: Doesn't conflict with other PostgreSQL installations
- ✅ **Portable**: Works on Windows, Mac, Linux
- ✅ **Version-locked**: Always PostgreSQL 16
- ✅ **Easy cleanup**: Remove everything with one command

You're now ready to use PostgreSQL 16 with Docker!

---

## Next Steps

1. [Database Schema Reference](./database_schema_reference.md) - Detailed schema documentation
2. [Integration Testing](../04_testing/integration_testing.md) - Run database tests
3. [Environment Switching](./environment_switching.md) - Switch between dev/test/prod
