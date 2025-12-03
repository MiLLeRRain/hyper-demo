#!/usr/bin/env python3
"""Simple database connectivity and basic operations test."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from sqlalchemy import text
from trading_bot.infrastructure.database import DatabaseManager


def main():
    """Test database connection."""
    load_dotenv()

    print("=" * 70)
    print("  Database Connection Test")
    print("=" * 70)

    # Get database config
    db_user = os.getenv("DB_USER", "trading_bot")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "trading_bot")

    if not db_password:
        print("\n[WARNING] DB_PASSWORD not set in .env")
        print("  Database tests will be skipped")
        print("\n  To enable database tests:")
        print("  1. Install PostgreSQL")
        print("  2. Create database: createdb trading_bot")
        print("  3. Set DB_PASSWORD in .env")
        return 0

    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    print(f"\n  Connecting to: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")

    try:
        # Initialize DatabaseManager
        db_manager = DatabaseManager(db_url)
        engine = db_manager.engine

        # Test connection
        with engine.connect() as conn:
            # Check PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"  [OK] Connected successfully!")
            print(f"       PostgreSQL version: {version.split(',')[0]}")

            # Check if our tables exist
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('trading_agents', 'agent_decisions', 'agent_trades', 'agent_performance')
            """))
            table_count = result.scalar()

            if table_count > 0:
                print(f"\n  [OK] Found {table_count} trading bot tables")

                # Get table names
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename LIKE 'agent%' OR tablename LIKE 'trading%'
                    ORDER BY tablename
                """))
                tables = [row[0] for row in result]
                print(f"       Tables: {', '.join(tables)}")

                # Get row counts
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        print(f"       - {table}: {count} rows")
                    except:
                        pass

            else:
                print(f"\n  [INFO] No tables found - run migrations first:")
                print(f"         alembic upgrade head")

        print("\n" + "=" * 70)
        print("  [SUCCESS] Database is accessible!")
        print("=" * 70)
        print("\n  Next steps:")
        print("  1. Run migrations: alembic upgrade head")
        print("  2. Test with full integration test")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("\n  Troubleshooting:")
        print("  1. Check if PostgreSQL is running:")
        print("     - Windows: Check Services for 'postgresql'")
        print("     - Linux/Mac: systemctl status postgresql")
        print("\n  2. Check database exists:")
        print(f"     psql -U {db_user} -l | grep {db_name}")
        print("\n  3. Create database if needed:")
        print(f"     createdb -U {db_user} {db_name}")
        print("\n  4. Verify credentials in .env")
        return 1


if __name__ == "__main__":
    sys.exit(main())
