from api.database import fetch_all, fetch_one, fetch_value

INDUSTRY_FILTER = "(CAST(:industry AS text) IS NULL OR sector_code = CAST(:industry AS text))"

BREAKDOWNS = {
    "email-type": (
        "gold.email_mix",
        "email_type",
        "array_position(ARRAY['Named contact', 'Generic inbox', 'Personal mailbox'], email_type)",
    ),
    "company-size": (
        "gold.size_mix",
        "company_size",
        "array_position(ARRAY['Micro (1-10)', 'Small (11-49)', 'Medium (50-199)', 'Large (200+)', 'Unknown'], company_size)",
    ),
    "turnover-band": ("gold.turnover_mix", "turnover_band", "turnover_band"),
    "sic-division": ("gold.division_summary", "sic_division", "leads DESC"),
    "job-role": ("gold.role_mix", "job_role", "leads DESC"),
}


def industries():
    return fetch_all("""
        SELECT sector_code, industry, leads, companies, callable_leads, tps_leads,
               ROUND(100.0 * tps_leads / NULLIF(leads, 0), 1) AS tps_rate
        FROM gold.industry_summary
        ORDER BY leads DESC
    """)


def industry(code):
    return fetch_one("""
        SELECT sector_code, industry, leads, companies, callable_leads, tps_leads,
               ROUND(100.0 * tps_leads / NULLIF(leads, 0), 1) AS tps_rate
        FROM gold.industry_summary
        WHERE sector_code = :code
    """, code=code)


def overview(industry=None):
    return fetch_one(f"""
        SELECT COALESCE(SUM(leads), 0) AS leads,
               COALESCE(SUM(companies), 0) AS companies,
               COALESCE(SUM(callable_leads), 0) AS callable_leads,
               COALESCE(SUM(tps_leads), 0) AS tps_leads,
               ROUND(100.0 * SUM(tps_leads) / NULLIF(SUM(leads), 0), 1) AS tps_rate
        FROM gold.industry_summary
        WHERE {INDUSTRY_FILTER}
    """, industry=industry)


def locations(industry=None):
    return fetch_all(f"""
        SELECT town, postcode_area, latitude, longitude, SUM(leads) AS leads
        FROM gold.location_summary
        WHERE {INDUSTRY_FILTER} AND latitude IS NOT NULL
        GROUP BY town, postcode_area, latitude, longitude
        ORDER BY leads DESC
    """, industry=industry)


def top_towns(industry=None, limit=10):
    return fetch_all(f"""
        SELECT town AS label, SUM(leads) AS leads
        FROM gold.location_summary
        WHERE {INDUSTRY_FILTER} AND town IS NOT NULL
        GROUP BY town
        ORDER BY leads DESC
        LIMIT :limit
    """, industry=industry, limit=limit)


def breakdown(dimension, industry=None, limit=50):
    table, column, order = BREAKDOWNS[dimension]
    return fetch_all(f"""
        SELECT {column} AS label, SUM(leads) AS leads
        FROM {table}
        WHERE {INDUSTRY_FILTER}
        GROUP BY {column}
        ORDER BY {order}
        LIMIT :limit
    """, industry=industry, limit=limit)


def turnover_comparison(industry=None):
    return fetch_all(f"""
        WITH bands AS (
            SELECT turnover_band,
                   SUM(leads) FILTER (WHERE {INDUSTRY_FILTER}) AS selected,
                   SUM(leads) AS overall
            FROM gold.turnover_mix
            GROUP BY turnover_band
        )
        SELECT turnover_band,
               COALESCE(ROUND(100.0 * selected / NULLIF(SUM(selected) OVER (), 0), 1), 0) AS selected_pct,
               ROUND(100.0 * overall / SUM(overall) OVER (), 1) AS all_pct
        FROM bands
        ORDER BY turnover_band
    """, industry=industry)


def incorporations(industry=None):
    return fetch_all(f"""
        WITH years AS (
            SELECT generate_series(MIN(year), MAX(year)) AS year
            FROM gold.incorporations
        )
        SELECT y.year, COALESCE(SUM(i.companies), 0) AS companies
        FROM years y
        LEFT JOIN gold.incorporations i
          ON i.year = y.year AND (CAST(:industry AS text) IS NULL OR i.sector_code = CAST(:industry AS text))
        GROUP BY y.year
        ORDER BY y.year
    """, industry=industry)


def pipeline_stages():
    return fetch_all("""
        SELECT layer, step, stage, row_count, loaded_at
        FROM public.etl_stages
        ORDER BY array_position(ARRAY['bronze', 'silver', 'gold'], layer), step
    """)


def gold_table_columns():
    rows = fetch_all("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'gold'
        ORDER BY table_name, ordinal_position
    """)
    tables = {}
    for row in rows:
        tables.setdefault(row["table_name"], []).append(row["column_name"])
    return tables


def gold_tables():
    return [
        {"name": name, "columns": columns, "row_count": fetch_value(f'SELECT COUNT(*) FROM gold."{name}"')}
        for name, columns in gold_table_columns().items()
    ]


def gold_rows(table, columns, industry=None, limit=100, offset=0):
    where = INDUSTRY_FILTER if "sector_code" in columns else "TRUE"
    total = fetch_value(f'SELECT COUNT(*) FROM gold."{table}" WHERE {where}', industry=industry)
    rows = fetch_all(f"""
        SELECT * FROM gold."{table}"
        WHERE {where}
        ORDER BY 1, 2
        LIMIT :limit OFFSET :offset
    """, industry=industry, limit=limit, offset=offset)
    return {"table": table, "total": total, "limit": limit, "offset": offset, "rows": rows}
