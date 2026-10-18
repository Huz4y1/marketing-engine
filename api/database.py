from sqlalchemy import create_engine, text

from etl.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-c default_transaction_read_only=on -c statement_timeout=5000"},
    pool_pre_ping=True,
)


def fetch_all(sql, **params):
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(text(sql), params).mappings()]


def fetch_one(sql, **params):
    rows = fetch_all(sql, **params)
    return rows[0] if rows else None


def fetch_value(sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()
