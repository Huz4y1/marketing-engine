from pyspark.sql import functions as F


def leads_by(leads, *dimensions):
    return leads.groupBy("sector_code", *dimensions).agg(F.count("*").alias("leads"))


def industry_summary(leads):
    return leads.groupBy("sector_code", "industry").agg(
        F.count("*").alias("leads"),
        F.countDistinct("company").alias("companies"),
        F.sum(F.when(~F.col("tps_registered"), 1).otherwise(0)).alias("callable_leads"),
        F.sum(F.col("tps_registered").cast("int")).alias("tps_leads"),
    )


def incorporations(leads):
    return (
        leads.where(F.col("incorporation_date").isNotNull())
        .groupBy("sector_code", F.year("incorporation_date").alias("year"))
        .agg(F.count("*").alias("companies"))
    )


def build_marts(leads):
    return {
        "industry_summary": industry_summary(leads),
        "location_summary": leads_by(leads, "postcode_area", "town", "latitude", "longitude"),
        "email_mix": leads_by(leads, "email_type"),
        "size_mix": leads_by(leads, "company_size"),
        "turnover_mix": leads_by(leads, "turnover_band"),
        "division_summary": leads_by(leads, "sic_division"),
        "role_mix": leads_by(leads, "job_role"),
        "incorporations": incorporations(leads),
    }
