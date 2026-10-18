from etl.common.spark import get_spark
from etl.config import DATABASE_URL
from etl.jobs import bronze_ingest, gold_marts, silver_leads

JOBS = [bronze_ingest, silver_leads, gold_marts]


def main():
    spark = get_spark()
    try:
        for job in JOBS:
            job.run(spark)
    finally:
        spark.stop()
    print(f"Pipeline finished: bronze, silver and gold schemas loaded into {DATABASE_URL.database}")


if __name__ == "__main__":
    main()
