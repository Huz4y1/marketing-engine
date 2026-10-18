import os
import sys
import urllib.request
from functools import reduce
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent
BRONZE = ROOT / "data" / "bronze"
JDBC_JAR = ROOT / "jars" / "postgresql-42.7.4.jar"
JDBC_JAR_URL = "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar"
DATABASE_URL = make_url(
    os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/marketing_engine")
)
SECTOR_G = "G - Wholesale And Retail Trade, Repair Of Motor Vehicles And Motorcycles"

RENAME_MAP = {
    "CompanyName": "Company",
    "TelephoneNumber": "Telephone",
    "Firstname": "Fname",
    "Surname": "Sname",
    "Role": "Contact_JobRole",
    "Email": "email",
    "EmployeeBand": "Emps",
    "TurnoverBand": "TO",
}


def jdbc_driver():
    if not JDBC_JAR.exists():
        JDBC_JAR.parent.mkdir(exist_ok=True)
        urllib.request.urlretrieve(JDBC_JAR_URL, JDBC_JAR)
    return str(JDBC_JAR)


def extract(spark):
    tables = []
    for path in sorted(BRONZE.glob("table_*.csv")):
        table = spark.read.option("header", True).option("delimiter", ",").csv(str(path))
        for old_name, new_name in RENAME_MAP.items():
            if old_name in table.columns:
                table = table.withColumnRenamed(old_name, new_name)
        tables.append(table.withColumn("source_table", F.lit(path.stem)))
    if not tables:
        sys.exit(f"No bronze CSVs in {BRONZE}. Run etl/generate_fake_data.py first.")
    return reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), tables)


def transform(raw):
    stages = [("extracted", raw.count())]

    in_sector = raw.filter(F.col("SICSector") == SECTOR_G)
    stages.append(("wholesale_retail_only", in_sector.count()))

    digits = F.regexp_replace("Telephone", r"\D", "")
    phone = F.when(digits.startswith("44"), F.concat(F.lit("0"), digits.substr(3, 20))).otherwise(digits)
    email = F.lower(F.trim("email"))
    website = F.regexp_replace(F.lower(F.trim("Website")), r"^https?://|/$", "")
    postcode = F.upper(F.trim("Postcode"))

    cleaned = in_sector.select(
        "source_table",
        F.trim("Company").alias("company"),
        F.trim("Town").alias("town"),
        F.trim("County").alias("county"),
        postcode.alias("postcode"),
        F.regexp_extract(postcode, r"^([A-Z]{1,2})\d", 1).alias("postcode_area"),
        F.when(F.length(phone) == 11, phone).alias("telephone"),
        (F.col("TPS").eqNullSafe("Y") | F.col("cTPS").eqNullSafe("Y")).alias("tps_registered"),
        F.trim("Title").alias("title"),
        F.initcap(F.trim("Fname")).alias("first_name"),
        F.initcap(F.trim("Sname")).alias("last_name"),
        F.trim("Contact_JobRole").alias("job_role"),
        F.when(email.rlike(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$"), email).alias("email"),
        F.when(website.rlike(r"^[a-z0-9.-]+\.[a-z]{2,}$"), website).alias("website"),
        F.col("SIC2").alias("sic_division"),
        F.col("SIC5").alias("sic_class"),
        F.col("Emps").alias("employee_band"),
        F.col("TO").alias("turnover_band"),
        F.to_date("Incorporation_Date").alias("incorporation_date"),
    )

    contactable = cleaned.na.drop(subset=["email", "telephone", "website"])
    stages.append(("valid_contact_details", contactable.count()))

    leads = contactable.dropDuplicates(["email"])
    stages.append(("deduplicated", leads.count()))

    return leads, stages


def ensure_database():
    admin = create_engine(DATABASE_URL.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": DATABASE_URL.database})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{DATABASE_URL.database}"'))
    admin.dispose()


def load(leads, stages):
    ensure_database()

    jdbc_url = f"jdbc:postgresql://{DATABASE_URL.host}:{DATABASE_URL.port or 5432}/{DATABASE_URL.database}"
    properties = {
        "user": DATABASE_URL.username,
        "password": DATABASE_URL.password or "",
        "driver": "org.postgresql.Driver",
    }
    leads.write.jdbc(jdbc_url, "leads", mode="overwrite", properties=properties)

    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE leads ADD PRIMARY KEY (email)"))
        conn.execute(text("DROP TABLE IF EXISTS etl_stages"))
        conn.execute(text("""
            CREATE TABLE etl_stages (
                step INT PRIMARY KEY,
                stage TEXT NOT NULL,
                row_count BIGINT NOT NULL,
                loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        conn.execute(
            text("INSERT INTO etl_stages (step, stage, row_count) VALUES (:step, :stage, :row_count)"),
            [{"step": i, "stage": stage, "row_count": count} for i, (stage, count) in enumerate(stages, start=1)],
        )
    engine.dispose()


def main():
    spark = (
        SparkSession.builder
        .appName("marketing-engine")
        .master("local[*]")
        .config("spark.driver.extraClassPath", jdbc_driver())
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    leads, stages = transform(extract(spark))
    load(leads, stages)

    for stage, count in stages:
        print(f"{stage:<24}{count:>8}")
    print(f"Loaded {stages[-1][1]} leads into {DATABASE_URL.database}.leads")

    spark.stop()


if __name__ == "__main__":
    main()
