SECTORS = {
    "A": {
        "name": "A - Agriculture, Forestry And Fishing",
        "weight": 6, "size_bias": 0.85, "tps": 0.20, "personal_email": 0.35,
        "trades": ["Farms", "Agriculture", "Dairies", "Growers", "Forestry"],
        "boost": {"NR": 6, "EX": 5, "PL": 4, "AB": 4, "YO": 4, "IV": 6, "HU": 3, "IP": 4, "DD": 3,
                  "E": 0.05, "EC": 0, "N": 0.05, "SE": 0.05, "SW": 0.05, "W": 0.05, "M": 0.3, "B": 0.3},
        "divisions": {
            "01 - Crop and animal production, hunting and related service activities": [
                "01110 - Growing of cereals (except rice), leguminous crops and oil seeds",
                "01410 - Raising of dairy cattle",
                "01500 - Mixed farming",
            ],
            "02 - Forestry and logging": ["02100 - Silviculture and other forestry activities"],
        },
    },
    "C": {
        "name": "C - Manufacturing",
        "weight": 9, "size_bias": 1.15, "tps": 0.10, "personal_email": 0.08,
        "trades": ["Engineering", "Fabrications", "Foods", "Manufacturing", "Precision"],
        "boost": {"B": 2.5, "S": 2.5, "ST": 3, "DE": 2.5, "CV": 2, "TS": 2, "LE": 1.5, "EC": 0.2},
        "divisions": {
            "10 - Manufacture of food products": [
                "10710 - Manufacture of bread; manufacture of fresh pastry goods and cakes",
                "10890 - Manufacture of other food products n.e.c.",
            ],
            "25 - Manufacture of fabricated metal products, except machinery and equipment": [
                "25110 - Manufacture of metal structures and parts of structures",
                "25620 - Machining",
            ],
            "28 - Manufacture of machinery and equipment n.e.c.": [
                "28990 - Manufacture of other special-purpose machinery n.e.c.",
            ],
        },
    },
    "F": {
        "name": "F - Construction",
        "weight": 12, "size_bias": 0.92, "tps": 0.14, "personal_email": 0.25,
        "trades": ["Construction", "Builders", "Electrical", "Plumbing", "Roofing"],
        "boost": {},
        "divisions": {
            "41 - Construction of buildings": [
                "41201 - Construction of commercial buildings",
                "41202 - Construction of domestic buildings",
            ],
            "43 - Specialised construction activities": [
                "43210 - Electrical installation",
                "43220 - Plumbing, heat and air-conditioning installation",
                "43390 - Other building completion and finishing",
            ],
        },
    },
    "G": {
        "name": "G - Wholesale And Retail Trade, Repair Of Motor Vehicles And Motorcycles",
        "weight": 18, "size_bias": 1.0, "tps": 0.13, "personal_email": 0.12,
        "trades": ["Motors", "Wholesale", "Retail", "Stores", "Distribution", "Auto Parts"],
        "boost": {},
        "divisions": {
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
    },
    "H": {
        "name": "H - Transportation And Storage",
        "weight": 7, "size_bias": 1.1, "tps": 0.11, "personal_email": 0.12,
        "trades": ["Logistics", "Haulage", "Couriers", "Freight", "Transport"],
        "boost": {"B": 2, "CV": 2.5, "DE": 2, "NG": 2, "SO": 2.5, "HU": 2.5, "IP": 2, "EC": 0.3},
        "divisions": {
            "49 - Land transport and transport via pipelines": [
                "49410 - Freight transport by road",
                "49320 - Taxi operation",
            ],
            "52 - Warehousing and support activities for transportation": [
                "52103 - Operation of warehousing and storage facilities for land transport activities",
                "52290 - Other transportation support activities",
            ],
            "53 - Postal and courier activities": ["53202 - Unlicensed carrier"],
        },
    },
    "I": {
        "name": "I - Accommodation And Food Service Activities",
        "weight": 9, "size_bias": 0.9, "tps": 0.16, "personal_email": 0.20,
        "trades": ["Hotel", "Kitchen", "Cafe", "Inns", "Catering"],
        "boost": {"BN": 3, "EH": 2.5, "YO": 3, "EX": 2, "PL": 2, "IV": 2, "W": 2},
        "divisions": {
            "55 - Accommodation": ["55100 - Hotels and similar accommodation"],
            "56 - Food and beverage service activities": [
                "56101 - Licensed restaurants",
                "56102 - Unlicensed restaurants and cafes",
                "56302 - Public houses and bars",
            ],
        },
    },
    "J": {
        "name": "J - Information And Communication",
        "weight": 10, "size_bias": 1.03, "tps": 0.07, "personal_email": 0.06,
        "trades": ["Digital", "Software", "Tech", "Media", "Systems"],
        "boost": {"EC": 4, "E": 3, "N": 2, "M": 2, "RG": 3, "CB": 3, "OX": 2, "BS": 1.5, "EH": 1.5},
        "divisions": {
            "62 - Computer programming, consultancy and related activities": [
                "62012 - Business and domestic software development",
                "62020 - Information technology consultancy activities",
                "62090 - Other information technology service activities",
            ],
            "63 - Information service activities": ["63120 - Web portals"],
        },
    },
    "K": {
        "name": "K - Financial And Insurance Activities",
        "weight": 7, "size_bias": 1.12, "tps": 0.06, "personal_email": 0.04,
        "trades": ["Capital", "Finance", "Insurance", "Wealth", "Partners"],
        "boost": {"EC": 8, "E": 3, "W": 2, "EH": 3, "LS": 2, "BT": 1.5, "CF": 1.5},
        "divisions": {
            "64 - Financial service activities, except insurance and pension funding": [
                "64999 - Financial intermediation not elsewhere classified",
            ],
            "66 - Activities auxiliary to financial services and insurance activities": [
                "66190 - Activities auxiliary to financial intermediation n.e.c.",
                "66220 - Activities of insurance agents and brokers",
            ],
        },
    },
    "M": {
        "name": "M - Professional, Scientific And Technical Activities",
        "weight": 14, "size_bias": 0.95, "tps": 0.09, "personal_email": 0.07,
        "trades": ["Consulting", "Accountants", "Solicitors", "Architects", "Associates"],
        "boost": {"EC": 3, "W": 2, "SW": 2, "M": 1.5, "BS": 1.5, "LS": 1.5},
        "divisions": {
            "69 - Legal and accounting activities": [
                "69102 - Solicitors",
                "69201 - Accounting and auditing activities",
            ],
            "70 - Activities of head offices; management consultancy activities": [
                "70229 - Management consultancy activities other than financial management",
            ],
            "71 - Architectural and engineering activities; technical testing and analysis": [
                "71111 - Architectural activities",
                "71129 - Other engineering activities",
            ],
        },
    },
    "Q": {
        "name": "Q - Human Health And Social Work Activities",
        "weight": 8, "size_bias": 1.08, "tps": 0.12, "personal_email": 0.10,
        "trades": ["Care", "Healthcare", "Dental", "Clinic", "Medical"],
        "boost": {"SA": 1.5, "PR": 1.5, "HU": 1.5},
        "divisions": {
            "86 - Human health activities": [
                "86210 - General medical practice activities",
                "86230 - Dental practice activities",
                "86900 - Other human health activities",
            ],
            "87 - Residential care activities": ["87100 - Residential nursing care facilities"],
            "88 - Social work activities without accommodation": [
                "88100 - Social work activities without accommodation for the elderly and disabled",
            ],
        },
    },
}

COMPANY_PREFIXES = [
    "Northern", "Apex", "Riverside", "Crown", "Summit", "Oakfield", "Harbour", "Pioneer", "Silverline",
    "Kingfisher", "Meadow", "Granite", "Beacon", "Elmwood", "Castle", "Phoenix", "Bluesky", "Redwood",
    "Highgate", "Lakeside", "Westbrook", "Ironbridge", "Foxglove", "Sterling", "Brightwater",
]
COMPANY_SUFFIXES = [" Ltd", " Limited", " Ltd", ""]
EMAIL_TLDS = [".co.uk", ".com", ".uk"]

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

STREETS = [
    "High Street", "Station Road", "Church Lane", "Mill Road", "Park Avenue", "Victoria Road",
    "Queens Road", "London Road", "Market Place", "King Street", "Bridge Street", "Albert Road",
]
ESTATES = ["Riverside Industrial Estate", "Enterprise Park", "Trade Centre", "Business Park", "Retail Park"]

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
TABLE_3_ROLES = ["Director", "Senior Decision Maker"]
TABLE_3_ROLE_WEIGHTS = [58, 42]

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
REPEAT_CONTACT_RATE = 0.03
DUPLICATE_ROW_RATE = 0.04
