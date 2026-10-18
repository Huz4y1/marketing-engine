from typing import Annotated

from fastapi import Query

IndustryFilter = Annotated[
    str | None,
    Query(pattern="^[A-Z]$", description="SIC section code to filter by, e.g. K for Finance & Insurance"),
]
