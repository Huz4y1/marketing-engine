import sys

from pyspark.sql import functions as F

from etl.common.database import prepare_database, record_stages, write_table
from etl.common.spark import get_spark
from etl.config import BRONZE_DIR


def read_source_file(spark, path):
    return (
        spark.read.option("header", True).option("delimiter", ",").csv(str(path))
        .withColumn("_source_file", F.lit(path.name))
        .withColumn("_ingested_at", F.current_timestamp())
    )


def run(spark):
    files = sorted(BRONZE_DIR.glob("table_*.csv"))
    if not files:
        sys.exit(f"No source CSVs in {BRONZE_DIR}. Run: python -m etl.source.generate_fake_data")

    prepare_database()
    total = 0
    for path in files:
        table = read_source_file(spark, path)
        write_table(table, f"bronze.{path.stem}")
        total += table.count()

    record_stages("bronze", [(f"Raw rows from {len(files)} source files", total)])


if __name__ == "__main__":
    run(get_spark("bronze-ingest"))
