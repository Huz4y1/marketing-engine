from functools import reduce

from pyspark.sql import functions as F

from etl.transforms import columns as c

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

REQUIRED_CONTACT_FIELDS = ["email", "telephone", "website"]


def harmonise(table):
    for old_name, new_name in RENAME_MAP.items():
        if old_name in table.columns:
            table = table.withColumnRenamed(old_name, new_name)
    return table


def union_sources(tables):
    labelled = [harmonise(table).withColumn("source_table", F.lit(name)) for name, table in tables.items()]
    return reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), labelled)


def standardise(raw):
    return raw.select(
        "source_table",
        c.sector_code("SICSector").alias("sector_code"),
        c.clean_text("SICSector").alias("sic_sector"),
        c.clean_text("Company").alias("company"),
        c.clean_text("Town").alias("town"),
        c.clean_text("County").alias("county"),
        c.postcode("Postcode").alias("postcode"),
        c.postcode_area(c.postcode("Postcode")).alias("postcode_area"),
        c.uk_phone("Telephone").alias("telephone"),
        (c.is_flagged("TPS") | c.is_flagged("cTPS")).alias("tps_registered"),
        c.clean_text("Title").alias("title"),
        F.initcap(c.clean_text("Fname")).alias("first_name"),
        F.initcap(c.clean_text("Sname")).alias("last_name"),
        F.coalesce(c.clean_text("Contact_JobRole"), F.lit("Not given")).alias("job_role"),
        c.email_address("email").alias("email"),
        c.website_domain("Website").alias("website"),
        c.clean_text("SIC2").alias("sic_division"),
        c.clean_text("SIC5").alias("sic_class"),
        F.coalesce(c.clean_text("Emps"), F.lit("U : Unknown")).alias("employee_band"),
        c.company_size("Emps").alias("company_size"),
        F.coalesce(c.clean_text("TO"), F.lit("U : Unknown")).alias("turnover_band"),
        F.to_date(c.clean_text("Incorporation_Date")).alias("incorporation_date"),
    ).withColumn("email_type", c.email_type("email"))


def enrich(leads, postcode_areas, industries):
    return (
        leads
        .join(F.broadcast(industries), "sector_code", "left")
        .withColumn("industry", F.coalesce("industry", "sic_sector"))
        .join(F.broadcast(postcode_areas), "postcode_area", "left")
        .withColumn("town", F.coalesce("town", "area_town"))
        .withColumn("county", F.coalesce("county", "area_county"))
        .drop("area_town", "area_county")
    )


def keep_contactable(leads):
    return leads.na.drop(subset=REQUIRED_CONTACT_FIELDS)


def deduplicate(leads):
    return leads.dropDuplicates(["email"])
