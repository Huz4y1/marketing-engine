import csv
import random
import re
from datetime import date, timedelta

from etl.config import BRONZE_DIR, REFERENCE_DIR
from etl.source.catalog import (
    COMPANY_PREFIXES,
    COMPANY_SUFFIXES,
    DUPLICATE_ROW_RATE,
    EMAIL_TLDS,
    EMPLOYEE_BANDS,
    EMPLOYEE_WEIGHTS,
    ESTATES,
    FIRST_NAMES,
    FREE_MAIL,
    PHONE_PREFIXES,
    POSTCODE_LETTERS,
    REPEAT_CONTACT_RATE,
    ROLE_WEIGHTS,
    ROLES,
    SECTORS,
    STANDARD_COLUMNS,
    STREETS,
    SURNAMES,
    TABLE_3_COLUMNS,
    TABLE_3_ROLE_WEIGHTS,
    TABLE_3_ROLES,
    TABLES,
    TITLE_WEIGHTS,
    TITLES,
    TURNOVER_BANDS,
    TURNOVER_WEIGHTS,
)

with open(REFERENCE_DIR / "postcode_areas.csv", newline="", encoding="utf-8") as f:
    PLACES = list(csv.DictReader(f))

SECTOR_CODES = list(SECTORS)
SECTOR_WEIGHTS = [s["weight"] for s in SECTORS.values()]
PLACE_WEIGHTS = {
    code: [float(p["weight"]) * s["boost"].get(p["postcode_area"], 1) for p in PLACES]
    for code, s in SECTORS.items()
}


def chance(p):
    return random.random() < p


def messy(value, p_upper=0.08, p_space=0.08):
    if chance(p_upper):
        value = value.upper()
    if chance(p_space):
        value = f"  {value} "
    return value


def biased_band(bands, weights, bias):
    scaled = [w * bias ** i for i, w in enumerate(weights[:-1])] + [weights[-1]]
    return random.choices(bands, scaled)[0]


def fake_phone():
    if chance(0.18):
        return ""
    number = random.choice(PHONE_PREFIXES) + f"{random.randint(0, 999):03d}"
    style = random.random()
    if style < 0.55:
        return number.replace(" ", "")
    if style < 0.75:
        return number
    if style < 0.93:
        return "+44 " + number[1:]
    return number.replace(" ", "")[:6]


def fake_email(first, last, domain, personal_rate):
    if chance(0.06):
        return ""
    if chance(personal_rate):
        email = f"{first}{last}{random.randint(1, 99)}@{random.choice(FREE_MAIL)}"
    elif chance(0.15):
        email = f"info@{domain}"
    else:
        email = f"{first}.{last}@{domain}"
    if chance(0.02):
        email = email.replace("@", "")
    return messy(email.lower())


def fake_website(domain):
    if chance(0.12):
        return ""
    url = random.choices([f"www.{domain}", f"http://www.{domain}", f"https://{domain}/"], [75, 15, 10])[0]
    return messy(url, p_upper=0.04, p_space=0.05)


def fake_postcode(area):
    return (
        f"{area}{random.randint(1, 28)} "
        f"{random.randint(1, 9)}{random.choice(POSTCODE_LETTERS)}{random.choice(POSTCODE_LETTERS)}"
    )


def fake_incorporation_date():
    if chance(0.05):
        return ""
    days = int(random.triangular(0, (date(2025, 12, 31) - date(1985, 1, 1)).days, 13000))
    return (date(1985, 1, 1) + timedelta(days=days)).isoformat()


def fake_lead():
    code = random.choices(SECTOR_CODES, SECTOR_WEIGHTS)[0]
    sector = SECTORS[code]
    sic2 = random.choice(list(sector["divisions"]))
    company = f"{random.choice(COMPANY_PREFIXES)} {random.choice(sector['trades'])}"
    domain = re.sub(r"[^a-z0-9]", "", company.lower()) + random.choice(EMAIL_TLDS)
    place = random.choices(PLACES, PLACE_WEIGHTS[code])[0]
    first, last = random.choice(FIRST_NAMES), random.choice(SURNAMES)
    return {
        "company": company + random.choice(COMPANY_SUFFIXES),
        "street": f"{random.randint(1, 240)} {random.choice(STREETS)}",
        "estate": random.choice(ESTATES) if chance(0.4) else "",
        "town": place["town"],
        "county": place["county"],
        "postcode": messy(fake_postcode(place["postcode_area"]), p_upper=0, p_space=0.05),
        "phone": fake_phone(),
        "tps": "Y" if chance(sector["tps"]) else "",
        "ctps": "Y" if chance(0.01) else "",
        "title": random.choices(TITLES, TITLE_WEIGHTS)[0],
        "first": first,
        "last": last,
        "email": fake_email(first, last, domain, sector["personal_email"]),
        "website": fake_website(domain),
        "sector": sector["name"],
        "sic2": sic2,
        "sic5": random.choice(sector["divisions"][sic2]),
        "employees": biased_band(EMPLOYEE_BANDS, EMPLOYEE_WEIGHTS, sector["size_bias"]),
        "turnover": biased_band(TURNOVER_BANDS, TURNOVER_WEIGHTS, sector["size_bias"]),
        "incorporated": fake_incorporation_date(),
    }


def standard_row(lead, email_column):
    return {
        "URN": random.randint(10_000_000, 99_999_999),
        "CompanyregNo": f"SC{random.randint(100000, 999999)}" if chance(0.05) else f"{random.randint(1, 16_999_999):08d}",
        "Company": lead["company"],
        "Ad1": lead["street"],
        "Ad2": lead["estate"],
        "Ad3": "",
        "Ad4": "",
        "Town": lead["town"],
        "County": lead["county"],
        "Postcode": lead["postcode"],
        "Telephone": lead["phone"],
        "TPS": lead["tps"],
        "cTPS": lead["ctps"],
        "Title": lead["title"],
        "Fname": lead["first"],
        "Sname": lead["last"],
        "Contact_JobRole": random.choices(ROLES, ROLE_WEIGHTS)[0],
        email_column: lead["email"],
        "Website": lead["website"],
        "SICSector": lead["sector"],
        "SIC2": lead["sic2"],
        "SIC5": lead["sic5"],
        "Emps": lead["employees"],
        "TO": lead["turnover"],
        "Incorporation_Date": lead["incorporated"],
    }


def table_3_row(lead):
    return {
        "ID": random.randint(1_000_000, 999_999_999),
        "CompanyName": lead["company"],
        "Address1": lead["street"],
        "Address2": lead["estate"],
        "Address3": lead["town"],
        "Address4": lead["county"],
        "Address5": "",
        "Address6": "",
        "Postcode": lead["postcode"],
        "TelephoneNumber": lead["phone"],
        "Title": lead["title"],
        "Firstname": lead["first"],
        "Surname": lead["last"],
        "Role": random.choices(TABLE_3_ROLES, TABLE_3_ROLE_WEIGHTS)[0],
        "email": lead["email"],
        "Website": lead["website"],
        "SICSector": lead["sector"],
        "SIC2": lead["sic2"],
        "SIC5": lead["sic5"],
        "EmployeeBand": lead["employees"],
        "TurnoverBand": lead["turnover"],
    }


def write_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    random.seed(42)
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    seen = []
    for name, (size, email_column) in TABLES.items():
        leads = [random.choice(seen) if seen and chance(REPEAT_CONTACT_RATE) else fake_lead() for _ in range(size)]
        seen.extend(leads)
        if name == "table_3":
            columns, rows = TABLE_3_COLUMNS, [table_3_row(lead) for lead in leads]
        else:
            columns = [c.format(email=email_column) for c in STANDARD_COLUMNS]
            rows = [standard_row(lead, email_column) for lead in leads]
        rows += random.sample(rows, k=int(size * DUPLICATE_ROW_RATE))
        random.shuffle(rows)
        write_csv(BRONZE_DIR / f"{name}.csv", columns, rows)
        print(f"{name}.csv  {len(rows):>6} rows")


if __name__ == "__main__":
    main()
