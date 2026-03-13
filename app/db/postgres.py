import psycopg2
import psycopg2.pool
import psycopg2.extras
from app.core.config import settings

# Connection pool — min 2, max 10 connections
_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=settings.DATABASE_URL.strip(),
)


def get_conn():
    """Get a connection from the pool."""
    return _pool.getconn()


def put_conn(conn):
    """Return a connection to the pool."""
    _pool.putconn(conn)


def query(sql: str, params: tuple = None) -> list[dict]:
    """Execute a SELECT and return list of dicts."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        put_conn(conn)


def query_one(sql: str, params: tuple = None) -> dict | None:
    """Execute a SELECT and return a single dict or None."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        put_conn(conn)


def execute(sql: str, params: tuple = None) -> int:
    """Execute an INSERT/UPDATE/DELETE and return rowcount."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


def execute_returning(sql: str, params: tuple = None) -> dict | None:
    """Execute an INSERT ... RETURNING and return the row as dict."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


def execute_many(statements: list[tuple[str, tuple]]) -> None:
    """Execute multiple statements in a single transaction."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            for sql, params in statements:
                cur.execute(sql, params)
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)
