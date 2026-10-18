import os
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

STATIC = Path(__file__).resolve().parent / "static"
MAX_ROWS = 500

engine = create_engine(
    os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/marketing_engine"),
    connect_args={"options": "-c statement_timeout=5000"},
    pool_pre_ping=True,
)

QUERIES = {
    "headline": {
        "title": "Headline stats",
        "chart": "kpi",
        "sql": """SELECT COUNT(*) AS leads,
       COUNT(DISTINCT company) AS companies,
       COUNT(*) FILTER (WHERE NOT tps_registered) AS callable_leads,
       ROUND(100.0 * AVG(tps_registered::int), 1) AS "TPS registered %"
FROM leads""",
    },
    "etl_funnel": {
        "title": "ETL funnel (rows kept per stage)",
        "chart": "bar",
        "sql": """SELECT stage, row_count
FROM etl_stages
ORDER BY step""",
    },
    "by_division": {
        "title": "Leads by SIC division",
        "chart": "bar",
        "sql": """SELECT sic_division, COUNT(*) AS leads
FROM leads
GROUP BY sic_division
ORDER BY leads DESC""",
    },
    "top_classes": {
        "title": "Top SIC classes",
        "chart": "bar",
        "sql": """SELECT sic_class, COUNT(*) AS leads
FROM leads
GROUP BY sic_class
ORDER BY leads DESC
LIMIT 10""",
    },
    "by_county": {
        "title": "Top counties",
        "chart": "bar",
        "sql": """SELECT county, COUNT(*) AS leads
FROM leads
WHERE county IS NOT NULL
GROUP BY county
ORDER BY leads DESC
LIMIT 10""",
    },
    "by_employees": {
        "title": "Leads by employee band",
        "chart": "bar",
        "sql": """SELECT COALESCE(employee_band, 'U : Unknown') AS employee_band, COUNT(*) AS leads
FROM leads
GROUP BY 1
ORDER BY 1""",
    },
    "by_turnover": {
        "title": "Leads by turnover band",
        "chart": "bar",
        "sql": """SELECT COALESCE(turnover_band, 'U : Unknown') AS turnover_band, COUNT(*) AS leads
FROM leads
GROUP BY 1
ORDER BY 1""",
    },
    "by_role": {
        "title": "Contact job roles",
        "chart": "bar",
        "sql": """SELECT COALESCE(job_role, 'Not given') AS job_role, COUNT(*) AS leads
FROM leads
GROUP BY 1
ORDER BY leads DESC""",
    },
    "email_type": {
        "title": "Company vs personal email",
        "chart": "bar",
        "sql": """SELECT CASE
         WHEN split_part(email, '@', 2) IN ('gmail.com', 'hotmail.co.uk', 'outlook.com', 'yahoo.co.uk')
           THEN 'Personal mailbox'
         WHEN email LIKE 'info@%' THEN 'Generic company inbox'
         ELSE 'Named company address'
       END AS email_type,
       COUNT(*) AS leads
FROM leads
GROUP BY 1
ORDER BY leads DESC""",
    },
    "by_source": {
        "title": "Leads by source table",
        "chart": "bar",
        "sql": """SELECT source_table, COUNT(*) AS leads
FROM leads
GROUP BY source_table
ORDER BY source_table""",
    },
    "incorporations": {
        "title": "Companies incorporated per year",
        "chart": "column",
        "sql": """SELECT EXTRACT(YEAR FROM incorporation_date)::int AS year, COUNT(*) AS companies
FROM leads
WHERE incorporation_date IS NOT NULL
GROUP BY 1
ORDER BY 1""",
    },
}


class Query(BaseModel):
    sql: str


def run(sql):
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchmany(MAX_ROWS)]
    except SQLAlchemyError as e:
        raise HTTPException(400, str(getattr(e, "orig", None) or e).strip())
    return {"columns": columns, "rows": rows, "ms": round((time.perf_counter() - start) * 1000, 1)}


app = FastAPI(title="Marketing Engine Dashboard")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/queries")
def list_queries():
    return [{"key": key, **query} for key, query in QUERIES.items()]


@app.get("/api/queries/{key}")
def run_saved_query(key: str):
    if key not in QUERIES:
        raise HTTPException(404, "Unknown query")
    return run(QUERIES[key]["sql"])


@app.post("/api/sql")
def run_custom_query(query: Query):
    sql = query.sql.strip().rstrip(";").strip()
    if ";" in sql or not sql.lower().startswith(("select", "with")):
        raise HTTPException(400, "Only a single SELECT or WITH statement is allowed.")
    return run(sql)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
