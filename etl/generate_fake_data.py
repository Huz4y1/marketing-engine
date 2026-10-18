import csv
import random
import re
from datetime import date, timedelta
from pathlib import Path

BRONZE = Path(__file__).resolve().parent.parent / "data" / "bronze"

SECTORS = {
    "G - Wholesale And Retail Trade, Repair Of Motor Vehicles And Motorcycles": {
        "45 - Wholesale and retail trade and repair of motor vehicles and motorcycles": [
            "45111 - Sale of new cars and light motor vehicles",
            "45200 - Maintenance and repair of motor vehicles",
            "45320 - Retail trade of motor vehicle parts and accessories",
        ],
        "46 - Wholesale trade, except of motor vehicles and motorcycles": [
            "46390 - Non-specialised wholesale of food, beverages and tobacco",
            "46690 - Wholesale of other machinery and equipment",
            "46900 - Non-specialised wholesale trade",
        ],
        "47 - Retail trade, except of motor vehicles and motorcycles": [
            "47110 - Retail sale in non-specialised stores with food, beverages or tobacco predominating",
            "47710 - Retail sale of clothing in specialised stores",
            "47910 - Retail sale via mail order houses or via Internet",
        ],
    },
    "C - Manufacturing": {
        "25 - Manufacture of fabricated metal products, except machinery and equipment": ["25620 - Machining"],
    },
    "F - Construction": {
        "43 - Specialised construction activities": [
            "43210 - Electrical installation",
            "43220 - Plumbing, heat and air-conditioning installation",
        ],
    },
    "J - Information And Communication": {
        "62 - Computer programming, consultancy and related activities": [
            "62020 - Information technology consultancy activities",
        ],
    },
    "M - Professional, Scientific And Technical Activities": {
        "70 - Activities of head offices, management consultancy activities": [
            "70229 - Management consultancy activities other than financial management",
        ],
    },
}
SECTOR_WEIGHTS = [40, 12, 14, 14, 20]

TRADES = {
    "45": ["Motors", "Auto Parts", "Car Centre", "Garage", "Tyres"],
    "46": ["Wholesale", "Distribution", "Trading", "Supplies", "Imports"],
    "47": ["Retail", "Stores", "Boutique", "Online", "Outlet"],
}
OTHER_TRADES = ["Engineering", "Electrical", "Consulting", "Digital", "Solutions", "Plumbing"]
PREFIXES = [
    "Northern", "Apex", "Riverside", "Crown", "Summit", "Oakfield", "Harbour", "Pioneer", "Silverline",
    "Kingfisher", "Meadow", "Granite", "Beacon", "Elmwood", "Castle", "Phoenix", "Bluesky", "Redwood",
    "Highgate", "Lakeside", "Westbrook", "Ironbridge", "Foxglove", "Sterling", "Brightwater",
]

EMPLOYEE_BANDS = [
    "A : 1 to 5", "B : 6 to 10", "C : 11 to 19", "D : 20 to 49", "E : 50 to 99", "F : 100 to 199",
    "G : 200 to 350", "H : 350 to 500", "I : 500 to 1000", "J : 1000+", "U : Unknown",
]
EMPLOYEE_WEIGHTS = [45, 12, 7, 6, 3, 2, 1, 0.5, 0.5, 0.5, 22]
TURNOVER_BANDS = [
    "A - <£50k", "B - £50k - £100k", "C - £100k - £250k", "D - £250k - £500k", "E - £500k - £1M",
    "F - £1M - £5M", "G - £5M - £10M", "H - £10M - £20M", "I - £20M - £50M", "J - £50M+", "U : Unknown",
]
TURNOVER_WEIGHTS = [12, 8, 12, 8, 6, 10, 3, 2, 1, 1, 37]

PLACES = [
    ("London", "Greater London", ["E", "EC", "N", "SE", "SW", "W"], 18),
    ("Manchester", "Greater Manchester", ["M"], 8),
    ("Birmingham", "West Midlands", ["B"], 8),
    ("Coventry", "West Midlands", ["CV"], 3),
    ("Leeds", "West Yorkshire", ["LS"], 6),
    ("Bradford", "West Yorkshire", ["BD"], 3),
    ("Sheffield", "South Yorkshire", ["S"], 4),
    ("Liverpool", "Merseyside", ["L"], 5),
    ("Bristol", "Bristol", ["BS"], 5),
    ("Nottingham", "Nottinghamshire", ["NG"], 4),
    ("Leicester", "Leicestershire", ["LE"], 4),
    ("Newcastle upon Tyne", "Tyne and Wear", ["NE"], 4),
    ("Cardiff", "South Glamorgan", ["CF"], 3),
    ("Glasgow", "Lanarkshire", ["G"], 5),
    ("Edinburgh", "Midlothian", ["EH"], 4),
    ("Southampton", "Hampshire", ["SO"], 3),
    ("Norwich", "Norfolk", ["NR"], 2),
    ("Reading", "Berkshire", ["RG"], 3),
]
STREETS = [
    "High Street", "Station Road", "Church Lane", "Mill Road", "Park Avenue", "Victoria Road",
    "Queens Road", "London Road", "Market Place", "King Street", "Bridge Street", "Albert Road",
]
AREAS = ["Riverside Industrial Estate", "Enterprise Park", "Trade Centre", "Business Park", "Retail Park"]
FIRST_NAMES = [
    "James", "Oliver", "Mohammed", "Harry", "George", "Jack", "Noah", "Daniel", "Thomas", "William",
    "Sarah", "Emma", "Olivia", "Amelia", "Sophie", "Charlotte", "Aisha", "Hannah", "Priya", "Grace",
    "Liam", "Ethan", "Ryan", "Adam", "Chloe", "Laura", "Zara", "Ben", "Matthew", "Rachel",
]
SURNAMES = [
    "Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson", "Thomas", "Johnson",
    "Roberts", "Khan", "Patel", "Walker", "Wright", "Robinson", "Thompson", "White", "Hughes", "Edwards",
    "Green", "Hall", "Wood", "Ali", "Clarke", "Jackson", "Hussain", "Turner", "Hill", "Cooper",
]
TITLES = ["Mr", "Mrs", "Ms", "Miss", "Dr", ""]
TITLE_WEIGHTS = [70, 11, 8, 4, 1, 6]
ROLES = ["PSC", "Director", "Proprietor", "Senior Decision Maker", ""]
ROLE_WEIGHTS = [65, 20, 4, 3, 5]
FREE_MAIL = ["gmail.com", "hotmail.co.uk", "outlook.com", "yahoo.co.uk"]
PHONE_PREFIXES = [
    "0113 496 0", "0114 496 0", "0115 496 0", "0116 496 0", "0117 496 0", "0118 496 0", "0121 496 0",
    "0131 496 0", "0141 496 0", "0151 496 0", "0161 496 0", "020 7946 0", "0191 498 0", "07700 900",
]
POSTCODE_LETTERS = "ABDEFGHJLNPQRSTUWXYZ"

STANDARD_COLUMNS = [
    "URN", "CompanyregNo", "Company", "Ad1", "Ad2", "Ad3", "Ad4", "Town", "County", "Postcode", "Telephone",
    "TPS", "cTPS", "Title", "Fname", "Sname", "Contact_JobRole", "{email}", "Website", "SICSector", "SIC2",
    "SIC5", "Emps", "TO", "Incorporation_Date",
]
TABLE_3_COLUMNS = [
    "ID", "CompanyName", "Address1", "Address2", "Address3", "Address4", "Address5", "Address6", "Postcode",
    "TelephoneNumber", "Title", "Firstname", "Surname", "Role", "email", "Website", "SICSector", "SIC2", "SIC5",
    "EmployeeBand", "TurnoverBand",
]
TABLES = {
    "table_1": (5000, "Email"),
    "table_2": (6000, "email"),
    "table_3": (9000, "email"),
    "table_4": (5000, "Email"),
    "table_5": (1000, "email"),
}


def chance(p):
    return random.random() < p


def messy(value, p_upper=0.08, p_space=0.08):
    if chance(p_upper):
        value = value.upper()
    if chance(p_space):
        value = f"  {value} "
    return value


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


def fake_email(first, last, domain):
    if chance(0.06):
        return ""
    style = random.random()
    if style < 0.75:
        email = f"{first}.{last}@{domain}"
    elif style < 0.88:
        email = f"info@{domain}"
    else:
        email = f"{first}{last}{random.randint(1, 99)}@{random.choice(FREE_MAIL)}"
    if chance(0.02):
        email = email.replace("@", "")
    return messy(email.lower())


def fake_website(domain):
    if chance(0.12):
        return ""
    url = random.choices([f"www.{domain}", f"http://www.{domain}", f"https://{domain}/"], [75, 15, 10])[0]
    return messy(url, p_upper=0.04, p_space=0.05)


def fake_postcode(prefixes):
    return (
        f"{random.choice(prefixes)}{random.randint(1, 28)} "
        f"{random.randint(1, 9)}{random.choice(POSTCODE_LETTERS)}{random.choice(POSTCODE_LETTERS)}"
    )


def fake_incorporation_date():
    if chance(0.05):
        return ""
    days = int(random.triangular(0, (date(2025, 12, 31) - date(1985, 1, 1)).days, 13000))
    return (date(1985, 1, 1) + timedelta(days=days)).isoformat()


def fake_lead():
    sector = random.choices(list(SECTORS), SECTOR_WEIGHTS)[0]
    sic2 = random.choice(list(SECTORS[sector]))
    trade = random.choice(TRADES.get(sic2[:2], OTHER_TRADES))
    company = f"{random.choice(PREFIXES)} {trade}"
    domain = re.sub(r"[^a-z0-9]", "", company.lower()) + random.choice([".co.uk", ".com", ".uk"])
    town, county, prefixes, _ = random.choices(PLACES, [p[3] for p in PLACES])[0]
    first, last = random.choice(FIRST_NAMES), random.choice(SURNAMES)
    return {
        "company": company + random.choice([" Ltd", " Limited", " Ltd", ""]),
        "street": f"{random.randint(1, 240)} {random.choice(STREETS)}",
        "area": random.choice(AREAS) if chance(0.4) else "",
        "town": town,
        "county": county,
        "postcode": messy(fake_postcode(prefixes), p_upper=0, p_space=0.05),
        "phone": fake_phone(),
        "tps": "Y" if chance(0.13) else "",
        "ctps": "Y" if chance(0.01) else "",
        "title": random.choices(TITLES, TITLE_WEIGHTS)[0],
        "first": first,
        "last": last,
        "email": fake_email(first, last, domain),
        "website": fake_website(domain),
        "sector": sector,
        "sic2": sic2,
        "sic5": random.choice(SECTORS[sector][sic2]),
        "employees": random.choices(EMPLOYEE_BANDS, EMPLOYEE_WEIGHTS)[0],
        "turnover": random.choices(TURNOVER_BANDS, TURNOVER_WEIGHTS)[0],
        "incorporated": fake_incorporation_date(),
    }


def standard_row(lead, email_column):
    return {
        "URN": random.randint(10_000_000, 99_999_999),
        "CompanyregNo": f"SC{random.randint(100000, 999999)}" if chance(0.05) else f"{random.randint(1, 16_999_999):08d}",
        "Company": lead["company"],
        "Ad1": lead["street"],
        "Ad2": lead["area"],
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
        "Address2": lead["area"],
        "Address3": lead["town"],
        "Address4": lead["county"],
        "Address5": "",
        "Address6": "",
        "Postcode": lead["postcode"],
        "TelephoneNumber": lead["phone"],
        "Title": lead["title"],
        "Firstname": lead["first"],
        "Surname": lead["last"],
        "Role": random.choices(["Director", "Senior Decision Maker"], [58, 42])[0],
        "email": lead["email"],
        "Website": lead["website"],
        "SICSector": lead["sector"],
        "SIC2": lead["sic2"],
        "SIC5": lead["sic5"],
        "EmployeeBand": lead["employees"],
        "TurnoverBand": lead["turnover"],
    }


def main():
    random.seed(42)
    BRONZE.mkdir(parents=True, exist_ok=True)
    seen = []
    for name, (size, email_column) in TABLES.items():
        leads = [random.choice(seen) if seen and chance(0.03) else fake_lead() for _ in range(size)]
        seen.extend(leads)
        if name == "table_3":
            columns, rows = TABLE_3_COLUMNS, [table_3_row(lead) for lead in leads]
        else:
            columns = [c.format(email=email_column) for c in STANDARD_COLUMNS]
            rows = [standard_row(lead, email_column) for lead in leads]
        rows += random.sample(rows, k=size // 25)
        random.shuffle(rows)
        with open(BRONZE / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{name}.csv  {len(rows):>6} rows")


if __name__ == "__main__":
    main()
