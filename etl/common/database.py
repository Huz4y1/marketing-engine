from sqlalchemy import create_engine, text

from etl.config import DATABASE_URL, JDBC_PROPERTIES, JDBC_URL, LAYERS

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def prepare_database():
    admin = create_engine(DATABASE_URL.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": DATABASE_URL.database})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{DATABASE_URL.database}"'))
    admin.dispose()

    with engine.begin() as conn:
        for schema in LAYERS:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.etl_stages (
                layer TEXT NOT NULL,
                step INT NOT NULL,
                stage TEXT NOT NULL,
                row_count BIGINT NOT NULL,
                loaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (layer, step)
            )
        """))


def list_tables(schema):
    with engine.connect() as conn:
        return conn.scalars(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = :schema ORDER BY table_name"),
            {"schema": schema},
        ).all()


def read_table(spark, table):
    return spark.read.jdbc(JDBC_URL, table, properties=JDBC_PROPERTIES)


def write_table(df, table):
    df.write.jdbc(JDBC_URL, table, mode="overwrite", properties=JDBC_PROPERTIES)


def execute(sql):
    with engine.begin() as conn:
        conn.execute(text(sql))


def record_stages(layer, stages):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM public.etl_stages WHERE layer = :layer"), {"layer": layer})
        conn.execute(
            text(
                "INSERT INTO public.etl_stages (layer, step, stage, row_count) "
                "VALUES (:layer, :step, :stage, :row_count)"
            ),
            [
                {"layer": layer, "step": step, "stage": stage, "row_count": count}
                for step, (stage, count) in enumerate(stages, start=1)
            ],
        )
    for stage, count in stages:
        print(f"{layer:<8}{stage:<40}{count:>8}")
