"""
Create PostgreSQL database if it doesn't exist. Run from backend dir:
  PYTHONPATH=. python scripts/create_db.py
Uses DATABASE_URL from .env; connects to default 'postgres' DB to create the target DB.
"""
import os
import sys

# Run from backend directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    from urllib.parse import urlparse
    from app.config import get_settings
    settings = get_settings()
    url = settings.database_url
    # postgresql+asyncpg://user:pass@host:port/dbname
    parsed = urlparse(url.replace("postgresql+asyncpg://", "postgresql://"))
    dbname = parsed.path.lstrip("/") or "instagram_automation"
    user = parsed.username or "postgres"
    password = parsed.password or "postgres"
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("Install psycopg2-binary: pip install psycopg2-binary")
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone():
            print(f"Database '{dbname}' already exists.")
        else:
            cur.execute(f'CREATE DATABASE "{dbname}"')
            print(f"Database '{dbname}' created.")
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
