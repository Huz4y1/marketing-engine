import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

STATIC = Path(__file__).resolve().parent / "static"
FILTER = ":industry IN ('ALL', sector_code)"

engine = create_engine(
    os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/marketing_engine"),
    connect_args={"options": "-c statement_timeout=5000"},
    pool_pre_ping=True,
)

CHARTS = {
    "kpis": {
        "title": "Overview",
        "chart": "kpi",
        "sql": f"""
            SELECT SUM(leads) AS leads,
                   SUM(companies) AS companies,
                   SUM(callable_leads) AS callable_leads,
                   ROUND(100.0 * SUM(tps_leads) / NULLIF(SUM(leads), 0), 1) AS "TPS registered %"
            FROM gold.industry_summary
            WHERE {FILTER}""",
    },
    "reachability": {
        "title": "Reachability",
        "chart": "donut",
        "sql": f"""
            SELECT 'Callable' AS status, SUM(callable_leads) AS leads
            FROM gold.industry_summary WHERE {FILTER}
            UNION ALL
            SELECT 'TPS registered', SUM(tps_leads)
            FROM gold.industry_summary WHERE {FILTER}""",
    },
    "email_mix": {
        "title": "Email type",
        "chart": "donut",
        "sql": f"""
            SELECT email_type, SUM(leads) AS leads
            FROM gold.email_mix
            WHERE {FILTER}
            GROUP BY email_type
            ORDER BY array_position(ARRAY['Named contact', 'Generic inbox', 'Personal mailbox'], email_type)""",
    },
    "size_mix": {
        "title": "Company size",
        "chart": "donut",
        "sql": f"""
            SELECT company_size, SUM(leads) AS leads
            FROM gold.size_mix
            WHERE {FILTER}
            GROUP BY company_size
            ORDER BY array_position(
                ARRAY['Micro (1-10)', 'Small (11-49)', 'Medium (50-199)', 'Large (200+)', 'Unknown'], company_size)""",
    },
    "map": {
        "title": "Lead locations",
        "chart": "map",
        "sql": f"""
            SELECT town, postcode_area, latitude, longitude, SUM(leads) AS leads
            FROM gold.location_summary
            WHERE {FILTER} AND latitude IS NOT NULL
            GROUP BY town, postcode_area, latitude, longitude
            ORDER BY leads DESC""",
    },
    "towns": {
        "title": "Top towns",
        "chart": "bar",
        "sql": f"""
            SELECT town, SUM(leads) AS leads
            FROM gold.location_summary
            WHERE {FILTER} AND town IS NOT NULL
            GROUP BY town
            ORDER BY leads DESC
            LIMIT 10""",
    },
    "industries": {
        "title": "Leads by industry",
        "chart": "rank",
        "sql": """
            SELECT sector_code, industry, leads
            FROM gold.industry_summary
            ORDER BY leads DESC""",
    },
    "tps_by_industry": {
        "title": "TPS-registered rate by industry",
        "chart": "rank",
        "sql": """
            SELECT sector_code, industry, ROUND(100.0 * tps_leads / NULLIF(leads, 0), 1) AS "TPS %"
            FROM gold.industry_summary
            ORDER BY 3 DESC""",
    },
    "turnover": {
        "title": "Turnover profile vs all industries",
        "chart": "compare",
        "sql": f"""
            WITH bands AS (
                SELECT turnover_band,
                       SUM(leads) FILTER (WHERE {FILTER}) AS selected,
                       SUM(leads) AS overall
                FROM gold.turnover_mix
                GROUP BY turnover_band
            )
            SELECT turnover_band,
                   ROUND(100.0 * COALESCE(selected, 0) / NULLIF(SUM(selected) OVER (), 0), 1) AS selected_pct,
                   ROUND(100.0 * overall / SUM(overall) OVER (), 1) AS all_pct
            FROM bands
            ORDER BY turnover_band""",
    },
    "divisions": {
        "title": "Top SIC divisions",
        "chart": "bar",
        "sql": f"""
            SELECT sic_division, SUM(leads) AS leads
            FROM gold.division_summary
            WHERE {FILTER}
            GROUP BY sic_division
            ORDER BY leads DESC
            LIMIT 8""",
    },
    "roles": {
        "title": "Contact job roles",
        "chart": "bar",
        "sql": f"""
            SELECT job_role, SUM(leads) AS leads
            FROM gold.role_mix
            WHERE {FILTER}
            GROUP BY job_role
            ORDER BY leads DESC""",
    },
    "incorporations": {
        "title": "Companies incorporated per year",
        "chart": "column",
        "sql": """
            WITH years AS (
                SELECT generate_series(MIN(year), MAX(year)) AS year
                FROM gold.incorporations
            )
            SELECT y.year, COALESCE(SUM(i.companies), 0) AS companies
            FROM years y
            LEFT JOIN gold.incorporations i
              ON i.year = y.year AND :industry IN ('ALL', i.sector_code)
            GROUP BY y.year
            ORDER BY y.year""",
    },
    "pipeline": {
        "title": "How the data was built",
        "chart": "pipeline",
        "sql": """
            SELECT layer, stage, row_count
            FROM public.etl_stages
            ORDER BY array_position(ARRAY['bronze', 'silver', 'gold'], layer), step""",
    },
}


def fetch(conn, sql, industry):
    result = conn.execute(text(sql), {"industry": industry})
    return {"columns": list(result.keys()), "rows": [list(row) for row in result]}


app = FastAPI(title="Marketing Engine Dashboard")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/dashboard")
def dashboard(industry: str = Query("ALL", pattern="^(ALL|[A-Z])$")):
    try:
        with engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            return [
                {"key": key, "title": chart["title"], "chart": chart["chart"], **fetch(conn, chart["sql"], industry)}
                for key, chart in CHARTS.items()
            ]
    except SQLAlchemyError as e:
        raise HTTPException(503, f"Database query failed: {getattr(e, 'orig', None) or e}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
