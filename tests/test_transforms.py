import os
import sys

import pytest
from pyspark.sql import SparkSession

from etl.transforms import columns, leads, marts


@pytest.fixture(scope="session")
def spark():
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    session = (
        SparkSession.builder
        .master("local[1]")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def apply(spark, rule, values):
    df = spark.createDataFrame([(v,) for v in values], "value string")
    return [row[0] for row in df.select(rule("value")).collect()]


def test_uk_phone_normalises_every_format(spark):
    assert apply(spark, columns.uk_phone, ["0113 496 0123", "+44 113 4960123", "01134960123", "01134", None]) == [
        "01134960123", "01134960123", "01134960123", None, None,
    ]


def test_email_address_is_trimmed_lowercased_and_validated(spark):
    assert apply(spark, columns.email_address, ["  Sarah.Khan@Apex.co.uk ", "sarah.khanapex.co.uk", None]) == [
        "sarah.khan@apex.co.uk", None, None,
    ]


def test_website_domain_strips_scheme_and_trailing_slash(spark):
    assert apply(spark, columns.website_domain, ["HTTP://www.apex.co.uk", "https://apex.com/", "not a site"]) == [
        "www.apex.co.uk", "apex.com", None,
    ]


def test_postcode_area_takes_leading_letters(spark):
    assert apply(spark, columns.postcode_area, ["LS12 4AB", "EC1 2BD", "M3 9ZZ", "12345"]) == ["LS", "EC", "M", None]


def test_company_size_groups_employee_bands(spark):
    assert apply(spark, columns.company_size, ["A : 1 to 5", "D : 20 to 49", "F : 100 to 199", "J : 1000+", "U : Unknown"]) == [
        "Micro (1-10)", "Small (11-49)", "Medium (50-199)", "Large (200+)", "Unknown",
    ]


def test_email_type_classifies_mailboxes(spark):
    assert apply(spark, columns.email_type, ["jo@gmail.com", "info@apex.com", "jo.bloggs@apex.com"]) == [
        "Personal mailbox", "Generic inbox", "Named contact",
    ]


def test_union_sources_harmonises_both_schemas(spark):
    table_1 = spark.createDataFrame([("Apex Ltd", "A@apex.com")], "Company string, Email string")
    table_3 = spark.createDataFrame([("Crown Ltd", "b@crown.com", "Director")], "CompanyName string, email string, Role string")

    combined = leads.union_sources({"table_1": table_1, "table_3": table_3})

    assert set(combined.columns) == {"Company", "email", "Contact_JobRole", "source_table"}
    assert sorted(row.source_table for row in combined.collect()) == ["table_1", "table_3"]


def test_contactable_and_deduplicated_leads(spark):
    df = spark.createDataFrame(
        [("a@x.com", "01134960123", "x.com"), ("a@x.com", "01134960123", "x.com"), ("b@y.com", None, "y.com")],
        "email string, telephone string, website string",
    )

    result = leads.deduplicate(leads.keep_contactable(df))

    assert [row.email for row in result.collect()] == ["a@x.com"]


def test_industry_summary_counts_callable_and_tps(spark):
    df = spark.createDataFrame(
        [("G", "Retail", "Apex", False), ("G", "Retail", "Apex", True), ("K", "Finance", "Crown", False)],
        "sector_code string, industry string, company string, tps_registered boolean",
    )

    rows = {row.sector_code: row for row in marts.industry_summary(df).collect()}

    assert (rows["G"].leads, rows["G"].companies, rows["G"].callable_leads, rows["G"].tps_leads) == (2, 1, 1, 1)
    assert (rows["K"].leads, rows["K"].callable_leads, rows["K"].tps_leads) == (1, 1, 0)
