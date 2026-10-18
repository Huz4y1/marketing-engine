import os
import sys
import urllib.request

from pyspark.sql import SparkSession

from etl.config import JARS_DIR, POSTGRES_DRIVER_VERSION, SHUFFLE_PARTITIONS

DRIVER_URL = "https://repo1.maven.org/maven2/org/postgresql/postgresql/{version}/postgresql-{version}.jar"


def postgres_driver():
    jar = JARS_DIR / f"postgresql-{POSTGRES_DRIVER_VERSION}.jar"
    if not jar.exists():
        JARS_DIR.mkdir(exist_ok=True)
        partial = jar.with_suffix(".part")
        urllib.request.urlretrieve(DRIVER_URL.format(version=POSTGRES_DRIVER_VERSION), partial)
        partial.replace(jar)
    return str(jar)


def get_spark(app_name="marketing-engine"):
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.driver.extraClassPath", postgres_driver())
        .config("spark.sql.shuffle.partitions", SHUFFLE_PARTITIONS)
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark
