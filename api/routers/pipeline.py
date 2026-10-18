from fastapi import APIRouter

from api import queries
from api.schemas import PipelineStage

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/stages", response_model=list[PipelineStage], summary="Row counts recorded by each ETL job")
def list_stages():
    return queries.pipeline_stages()
