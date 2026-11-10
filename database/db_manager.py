"""SQLite database utilities - Functional implementation."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, TypeVar
from contextlib import contextmanager
import pandas as pd

from config.settings import get_settings


# Type variables for generic functions
T = TypeVar('T')


def get_db_path() -> Path:
    """Get the database path from settings."""
    return get_settings().db_path_resolved


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    """Get SQLite connection with automatic commit/rollback.

    Args:
        db_path: Path to database file. If None, uses default from settings.
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


def query(sql: str, params: Optional[tuple] = None, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Run SELECT query and return results as list of dicts.

    Args:
        sql: SQL query string
        params: Query parameters
        db_path: Database path (optional, uses default if not provided)

    Returns:
        List of dictionaries containing query results
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, params or ())
        columns = [col[0] for col in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def execute(sql: str, params: Optional[tuple] = None, db_path: Optional[Path] = None) -> int:
    """Run INSERT/UPDATE/DELETE query and return affected row count.

    Args:
        sql: SQL statement
        params: Statement parameters
        db_path: Database path (optional, uses default if not provided)

    Returns:
        Number of affected rows
    """
    with get_connection(db_path) as conn:
        return conn.execute(sql, params or ()).rowcount


def to_dataframe(sql: str, params: Optional[tuple] = None, db_path: Optional[Path] = None) -> pd.DataFrame:
    """Execute query and return results as pandas DataFrame.

    Args:
        sql: SQL query string
        params: Query parameters
        db_path: Database path (optional, uses default if not provided)

    Returns:
        DataFrame containing query results
    """
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute_script(script_path: Path, db_path: Optional[Path] = None) -> None:
    """Execute SQL script file.

    Args:
        script_path: Path to SQL script file
        db_path: Database path (optional, uses default if not provided)
    """
    with open(script_path, 'r') as f:
        script_content = f.read()

    with get_connection(db_path) as conn:
        conn.executescript(script_content)


def with_transaction(func: Callable[[sqlite3.Connection], T], db_path: Optional[Path] = None) -> T:
    """Execute a function within a database transaction.

    Higher-order function that provides transactional safety for complex operations.

    Args:
        func: Function that takes a connection and returns a value
        db_path: Database path (optional, uses default if not provided)

    Returns:
        Result of the function
    """
    with get_connection(db_path) as conn:
        return func(conn)
