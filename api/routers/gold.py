from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api import queries
from api.params import IndustryFilter
from api.schemas import GoldRows, GoldTable

router = APIRouter(prefix="/api/gold", tags=["gold tables"])


@router.get("", response_model=list[GoldTable], summary="List the gold tables with their columns and row counts")
def list_gold_tables():
    return queries.gold_tables()


@router.get("/{table}", response_model=GoldRows, summary="Read rows from one gold table")
def read_gold_table(
    table: str,
    industry: IndustryFilter = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    tables = queries.gold_table_columns()
    if table not in tables:
        raise HTTPException(404, f"No gold table named {table!r}. Available: {', '.join(tables)}")
    return queries.gold_rows(table, tables[table], industry, limit, offset)
