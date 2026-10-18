from etl.common.database import read_table, record_stages, write_table
from etl.common.spark import get_spark
from etl.transforms.marts import build_marts


def run(spark):
    leads = read_table(spark, "silver.leads").cache()
    marts = build_marts(leads)

    total = 0
    for name, mart in marts.items():
        mart = mart.cache()
        write_table(mart, f"gold.{name}")
        total += mart.count()
        mart.unpersist()

    record_stages("gold", [(f"Rows across {len(marts)} gold tables", total)])
    leads.unpersist()


if __name__ == "__main__":
    run(get_spark("gold-marts"))
