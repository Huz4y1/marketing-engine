from pyspark.sql import Column
from pyspark.sql import functions as F

FREE_MAIL_DOMAINS = ["gmail.com", "hotmail.co.uk", "outlook.com", "yahoo.co.uk"]


def col(column):
    return column if isinstance(column, Column) else F.col(column)


def clean_text(column):
    value = F.trim(col(column))
    return F.when(value != "", value)


def uk_phone(column):
    digits = F.regexp_replace(col(column), r"\D", "")
    national = F.when(digits.startswith("44"), F.concat(F.lit("0"), digits.substr(3, 20))).otherwise(digits)
    return F.when(F.length(national) == 11, national)


def email_address(column):
    email = F.lower(F.trim(col(column)))
    return F.when(email.rlike(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$"), email)


def website_domain(column):
    site = F.regexp_replace(F.lower(F.trim(col(column))), r"^https?://|/$", "")
    return F.when(site.rlike(r"^[a-z0-9.-]+\.[a-z]{2,}$"), site)


def postcode(column):
    return F.upper(F.regexp_replace(F.trim(col(column)), r"\s+", " "))


def postcode_area(column):
    area = F.regexp_extract(col(column), r"^([A-Z]{1,2})\d", 1)
    return F.when(area != "", area)


def sector_code(column):
    return F.substring(F.trim(col(column)), 1, 1)


def is_flagged(column):
    return F.upper(F.trim(col(column))).eqNullSafe("Y")


def company_size(employee_band):
    band = F.substring(col(employee_band), 1, 1)
    return (
        F.when(band.isin("A", "B"), "Micro (1-10)")
        .when(band.isin("C", "D"), "Small (11-49)")
        .when(band.isin("E", "F"), "Medium (50-199)")
        .when(band.isin("G", "H", "I", "J"), "Large (200+)")
        .otherwise("Unknown")
    )


def email_type(email):
    email = col(email)
    return (
        F.when(F.split(email, "@")[1].isin(FREE_MAIL_DOMAINS), "Personal mailbox")
        .when(email.startswith("info@"), "Generic inbox")
        .otherwise("Named contact")
    )
