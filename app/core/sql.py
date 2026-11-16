from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

from app.core.config import settings
from app.sql.postgresql import QUERIES as POSTGRESQL_QUERIES


def sql_for(key: str, mysql_sql: str) -> TextClause:
    """
    Pick the SQL for the configured DB_TYPE.

    MySQL (default) runs `mysql_sql` exactly as written in the endpoint, unchanged since
    v1.2.0. PostgreSQL runs the translated query registered under `key` in
    app/sql/postgresql.py (same columns and aliases, so the endpoint code is shared).
    """
    if settings.is_postgresql:
        return text(POSTGRESQL_QUERIES[key])
    return text(mysql_sql)
