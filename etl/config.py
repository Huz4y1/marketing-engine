import os
from pathlib import Path

from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = ROOT / "data" / "bronze"
REFERENCE_DIR = ROOT / "etl" / "reference"
JARS_DIR = ROOT / "jars"

LAYERS = ("bronze", "silver", "gold")

DATABASE_URL = make_url(
    os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/marketing_engine")
)
JDBC_URL = f"jdbc:postgresql://{DATABASE_URL.host or 'localhost'}:{DATABASE_URL.port or 5432}/{DATABASE_URL.database}"
JDBC_PROPERTIES = {
    "user": DATABASE_URL.username or "",
    "password": DATABASE_URL.password or "",
    "driver": "org.postgresql.Driver",
}

POSTGRES_DRIVER_VERSION = "42.7.4"
SHUFFLE_PARTITIONS = "8"
