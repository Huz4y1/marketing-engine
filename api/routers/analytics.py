from enum import Enum
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from api import queries
from api.params import IndustryFilter
from api.schemas import Category, IndustrySummary, Location, Overview, TurnoverComparison, YearCount

router = APIRouter(prefix="/api", tags=["analytics"])


class Dimension(str, Enum):
    email_type = "email-type"
    company_size = "company-size"
    turnover_band = "turnover-band"
    sic_division = "sic-division"
    job_role = "job-role"


@router.get("/industries", response_model=list[IndustrySummary], summary="Every industry with its lead counts")
def list_industries():
    return queries.industries()


@router.get("/industries/{code}", response_model=IndustrySummary, summary="One industry by SIC section code")
def get_industry(code: Annotated[str, Path(pattern="^[A-Z]$")]):
    industry = queries.industry(code)
    if industry is None:
        raise HTTPException(404, f"No industry with code {code}")
    return industry


@router.get("/overview", response_model=Overview, summary="Headline totals")
def get_overview(industry: IndustryFilter = None):
    return queries.overview(industry)


@router.get("/locations", response_model=list[Location], summary="Leads per postcode area with coordinates")
def get_locations(industry: IndustryFilter = None):
    return queries.locations(industry)


@router.get("/towns", response_model=list[Category], summary="Towns with the most leads")
def get_top_towns(industry: IndustryFilter = None, limit: Annotated[int, Query(ge=1, le=100)] = 10):
    return queries.top_towns(industry, limit)


@router.get("/breakdowns/{dimension}", response_model=list[Category], summary="Lead counts split by one dimension")
def get_breakdown(
    dimension: Dimension,
    industry: IndustryFilter = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    return queries.breakdown(dimension.value, industry, limit)


@router.get(
    "/turnover/comparison",
    response_model=list[TurnoverComparison],
    summary="Turnover band mix of one industry against all industries",
)
def get_turnover_comparison(industry: IndustryFilter = None):
    return queries.turnover_comparison(industry)


@router.get("/incorporations", response_model=list[YearCount], summary="Companies incorporated per year")
def get_incorporations(industry: IndustryFilter = None):
    return queries.incorporations(industry)
