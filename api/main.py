import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from api.routers import analytics, gold, pipeline
from etl.config import ROOT

DASHBOARD = ROOT / "dashboard"

app = FastAPI(
    title="Marketing Engine API",
    description="Read-only REST API over the gold layer of the Marketing Engine ETL pipeline.",
    version="1.0.0",
)

for module in (analytics, gold, pipeline):
    app.include_router(module.router)

app.mount("/static", StaticFiles(directory=DASHBOARD), name="static")


@app.exception_handler(SQLAlchemyError)
def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503, content={"detail": f"Database query failed: {getattr(exc, 'orig', None) or exc}"})


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(DASHBOARD / "index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
