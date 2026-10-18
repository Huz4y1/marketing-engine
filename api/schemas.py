from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IndustrySummary(BaseModel):
    sector_code: str = Field(examples=["K"])
    industry: str = Field(examples=["Finance & Insurance"])
    leads: int
    companies: int
    callable_leads: int
    tps_leads: int
    tps_rate: float | None = Field(description="Percentage of leads registered with TPS or CTPS")


class Overview(BaseModel):
    leads: int
    companies: int
    callable_leads: int
    tps_leads: int
    tps_rate: float | None


class Location(BaseModel):
    town: str
    postcode_area: str
    latitude: float
    longitude: float
    leads: int


class Category(BaseModel):
    label: str
    leads: int


class TurnoverComparison(BaseModel):
    turnover_band: str
    selected_pct: float = Field(description="Share of the selected industry's leads in this band")
    all_pct: float = Field(description="Share of all leads in this band")


class YearCount(BaseModel):
    year: int
    companies: int


class PipelineStage(BaseModel):
    layer: str = Field(examples=["silver"])
    step: int
    stage: str
    row_count: int
    loaded_at: datetime


class GoldTable(BaseModel):
    name: str
    columns: list[str]
    row_count: int


class GoldRows(BaseModel):
    table: str
    total: int
    limit: int
    offset: int
    rows: list[dict[str, Any]]
