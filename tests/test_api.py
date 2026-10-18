import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from api import queries
from api.main import app

client = TestClient(app)

OVERVIEW = {"leads": 10, "companies": 4, "callable_leads": 9, "tps_leads": 1, "tps_rate": 10.0}


@pytest.fixture
def calls(monkeypatch):
    recorded = []

    def fake_overview(industry=None):
        recorded.append(industry)
        return OVERVIEW

    monkeypatch.setattr(queries, "overview", fake_overview)
    return recorded


def test_overview_without_filter_covers_all_industries(calls):
    response = client.get("/api/overview")

    assert response.status_code == 200
    assert response.json() == OVERVIEW
    assert calls == [None]


def test_overview_passes_the_industry_filter_to_the_query(calls):
    assert client.get("/api/overview?industry=K").status_code == 200
    assert calls == ["K"]


@pytest.mark.parametrize("industry", ["k", "KK", "1", "K;DROP"])
def test_invalid_industry_codes_are_rejected_before_any_query(calls, industry):
    assert client.get(f"/api/overview?industry={industry}").status_code == 422
    assert calls == []


def test_unknown_breakdown_dimension_is_rejected():
    assert client.get("/api/breakdowns/password").status_code == 422


def test_breakdown_forwards_dimension_and_limit(monkeypatch):
    seen = {}

    def fake_breakdown(dimension, industry=None, limit=50):
        seen.update(dimension=dimension, industry=industry, limit=limit)
        return [{"label": "Director", "leads": 3}]

    monkeypatch.setattr(queries, "breakdown", fake_breakdown)

    response = client.get("/api/breakdowns/job-role?industry=G&limit=5")

    assert response.json() == [{"label": "Director", "leads": 3}]
    assert seen == {"dimension": "job-role", "industry": "G", "limit": 5}


def test_unknown_industry_returns_404(monkeypatch):
    monkeypatch.setattr(queries, "industry", lambda code: None)

    assert client.get("/api/industries/Z").status_code == 404


def test_only_existing_gold_tables_can_be_read(monkeypatch):
    monkeypatch.setattr(queries, "gold_table_columns", lambda: {"industry_summary": ["sector_code", "leads"]})

    response = client.get("/api/gold/pg_shadow")

    assert response.status_code == 404
    assert "industry_summary" in response.json()["detail"]


def test_database_errors_become_503(monkeypatch):
    def broken(industry=None):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(queries, "overview", broken)

    response = client.get("/api/overview")

    assert response.status_code == 503
    assert "connection refused" in response.json()["detail"]
