import sys

from pyspark.sql import functions as F

from etl.common.database import execute, list_tables, read_table, record_stages, write_table
from etl.common.spark import get_spark
from etl.config import REFERENCE_DIR
from etl.transforms.leads import deduplicate, enrich, keep_contactable, standardise, union_sources


def read_reference(spark, name):
    return spark.read.option("header", True).csv(str(REFERENCE_DIR / name))


def load_reference(spark):
    postcode_areas = read_reference(spark, "postcode_areas.csv").select(
        "postcode_area",
        F.col("town").alias("area_town"),
        F.col("county").alias("area_county"),
        F.col("latitude").cast("double"),
        F.col("longitude").cast("double"),
    )
    industries = read_reference(spark, "industries.csv")
    return postcode_areas, industries


def run(spark):
    bronze = {name: read_table(spark, f"bronze.{name}") for name in list_tables("bronze")}
    if not bronze:
        sys.exit("The bronze layer is empty. Run: python -m etl.jobs.bronze_ingest")

    raw = union_sources(bronze)
    standardised = enrich(standardise(raw), *load_reference(spark))
    contactable = keep_contactable(standardised)
    leads = deduplicate(contactable).cache()

    write_table(leads, "silver.leads")
    execute("ALTER TABLE silver.leads ADD PRIMARY KEY (email)")

    record_stages("silver", [
        ("Rows read from bronze", raw.count()),
        ("Rows with valid contact details", contactable.count()),
        ("Unique leads", leads.count()),
    ])
    leads.unpersist()


if __name__ == "__main__":
    run(get_spark("silver-leads"))
