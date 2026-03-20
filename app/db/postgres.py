import logging
import psycopg2
import psycopg2.pool
import psycopg2.extras
from app.core.config import settings

logger = logging.getLogger("rchat.db")

_dsn = settings.DATABASE_URL.strip()

# Connection pool — lazy init so we can recreate after failures
_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=_dsn,
        )
    return _pool


def _safe_conn():
    """Get a connection from the pool, verifying it's alive."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        # Quick health check — detects stale SSL connections
        conn.isolation_level
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        # Reset to clean state if previous transaction left it dirty
        if conn.status != psycopg2.extensions.STATUS_READY:
            conn.rollback()
        return conn
    except Exception:
        # Connection is dead — close it and get a fresh one
        try:
            pool.putconn(conn, close=True)
        except Exception:
            pass
        # Recreate the entire pool if needed
        global _pool
        try:
            _pool.closeall()
        except Exception:
            pass
        _pool = None
        pool = _get_pool()
        return pool.getconn()


def _put_conn(conn):
    """Return a connection to the pool safely."""
    try:
        pool = _get_pool()
        if conn.closed:
            pool.putconn(conn, close=True)
        else:
            pool.putconn(conn)
    except Exception:
        pass


# Public aliases — used by services that need manual transaction control
get_conn = _safe_conn
put_conn = _put_conn


def query(sql: str, params: tuple = None) -> list[dict]:
    """Execute a SELECT and return list of dicts."""
    conn = _safe_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # Retry once with fresh connection
        _put_conn(conn)
        conn = _safe_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        _put_conn(conn)


def query_one(sql: str, params: tuple = None) -> dict | None:
    """Execute a SELECT and return a single dict or None."""
    conn = _safe_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        _put_conn(conn)
        conn = _safe_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        _put_conn(conn)


def execute(sql: str, params: tuple = None) -> int:
    """Execute an INSERT/UPDATE/DELETE and return rowcount."""
    conn = _safe_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        _put_conn(conn)
        conn = _safe_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        _put_conn(conn)


def execute_returning(sql: str, params: tuple = None) -> dict | None:
    """Execute an INSERT ... RETURNING and return the row as dict."""
    conn = _safe_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        _put_conn(conn)
        conn = _safe_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception:
        conn.rollback()
        raise
    finally:
        _put_conn(conn)


def execute_many(statements: list[tuple[str, tuple]]) -> None:
    """Execute multiple statements in a single transaction."""
    conn = _safe_conn()
    try:
        with conn.cursor() as cur:
            for sql, params in statements:
                cur.execute(sql, params)
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _put_conn(conn)
