# Docker Configuration

This directory contains Docker-related configuration files for the Trading Bot project.

## Files

### `init-db.sql`

PostgreSQL initialization script that runs automatically when the database container is first created.

**What it does:**
- Creates all 5 database tables with proper schema
- Sets up indexes for performance
- Adds check constraints for data validation
- Inserts sample data for development

**Customization:**
Edit this file to:
- Modify initial database schema
- Add more sample data
- Install PostgreSQL extensions
- Configure database settings

**Automatic Execution:**
This script runs only once when:
1. The container is first created
2. The data volume is empty

To re-run the script, you must delete the volume:
```bash
docker-compose down -v
docker-compose up -d postgres
```

---

## Usage

### Start Database

```bash
# From project root
docker-compose up -d postgres
```

### View Initialization Logs

```bash
docker-compose logs postgres
```

Look for:
```
✅ Created table: trading_agents
✅ Created table: agent_decisions
✅ Created table: agent_trades
✅ Created table: agent_performance
✅ Created table: bot_state
✅ Database initialization completed!
```

### Connect to Database

```bash
docker-compose exec postgres psql -U trading_bot -d trading_bot_dev
```

### Run Custom SQL Scripts

```bash
# Place your script in this directory
# Then run:
docker-compose exec -T postgres psql -U trading_bot -d trading_bot_dev < docker/your_script.sql
```

---

## Database Schema

The `init-db.sql` script creates:

1. **trading_agents** - AI agent configurations
2. **agent_decisions** - Trading decisions with reasoning
3. **agent_trades** - Executed trades and P&L
4. **agent_performance** - Performance snapshots
5. **bot_state** - System state for resume

See [Database Schema Reference](../docs/06_deployment/database_schema_reference.md) for detailed documentation.

---

## Backup Scripts

### `backup.sh` (optional)

Create this file for automated backups:

```bash
#!/bin/bash
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/trading_bot_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U trading_bot trading_bot_dev > $BACKUP_FILE

gzip $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

Run daily with cron:
```bash
chmod +x docker/backup.sh
crontab -e
# Add: 0 2 * * * /path/to/hyper-demo/docker/backup.sh
```

---

## Troubleshooting

### Script Not Running

If `init-db.sql` doesn't run:

1. Check logs:
   ```bash
   docker-compose logs postgres | grep -A 50 "initialization"
   ```

2. Verify volume is empty:
   ```bash
   docker volume inspect hyper-demo_postgres_data
   ```

3. Force re-initialization:
   ```bash
   docker-compose down -v  # ⚠️ Deletes all data
   docker-compose up -d postgres
   ```

### Permission Errors

On Linux, if you see permission errors:

```bash
sudo chown -R 999:999 ./docker
```

(User ID 999 is the postgres user in the container)

---

## Production Considerations

### Security

1. **Change default password** in `docker-compose.yml`
2. **Use Docker secrets** instead of environment variables
3. **Enable SSL/TLS** for connections
4. **Limit network access** with firewall rules

### Performance

1. **Tune PostgreSQL** with custom `postgresql.conf`:
   ```yaml
   volumes:
     - ./docker/postgresql.conf:/etc/postgresql/postgresql.conf:ro
   ```

2. **Increase shared_buffers** for better caching
3. **Configure connection pooling** with PgBouncer
4. **Regular VACUUM** to maintain performance

### Monitoring

1. **Set up pg_stat_statements** for query analysis
2. **Configure logging** for slow queries
3. **Monitor disk usage** with alerts
4. **Track connection counts** and pool exhaustion

---

## Additional Resources

- [Database Setup Guide](../docs/06_deployment/database_setup.md)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL 16 Documentation](https://www.postgresql.org/docs/16/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
