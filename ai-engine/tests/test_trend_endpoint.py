"""
HTTP-level tests for GET /trend and GET /risk, confirming the extended
TrendResponse schema (with `history`) actually reaches the client - a service
returning the right dict is not enough on its own, since FastAPI's
response_model silently drops any field the Pydantic schema doesn't declare.

Like test_trend_service.py, these patch services.trend_service's imported
list_analyses/load_analysis rather than using a real database.
"""

import services.trend_service as trend_service
from fastapi.testclient import TestClient
from main import app
from tests.test_trend_service import _analysis, _install_fake_history


def test_trend_endpoint_returns_history_field(monkeypatch):
    analyses = [
        _analysis("day1.csv", "2026-01-01T00:00:00+00:00", [(3, 0.0001, 0.00008, 0.00012)]),
        _analysis("day2.csv", "2026-01-02T00:00:00+00:00", [(3, 0.00012, 0.0001, 0.00014)]),
    ]
    _install_fake_history(monkeypatch, analyses)

    with TestClient(app) as client:
        response = client.get("/trend", params={"days": 2})

    assert response.status_code == 200
    body = response.json()

    (trend,) = body["trends"]
    # If schemas.QubitTrend didn't declare `history`, this key would be
    # silently stripped by response_model filtering rather than missing with
    # an error - so its presence here is the real regression check.
    assert "history" in trend
    assert trend["history"] == [
        {"analysis_filename": "saved_0.json", "filename": "day1.csv",
         "analyzed_at": "2026-01-01T00:00:00+00:00",
         "qsfi": 0.0001, "t1": 0.00008, "t2": 0.00012},
        {"analysis_filename": "saved_1.json", "filename": "day2.csv",
         "analyzed_at": "2026-01-02T00:00:00+00:00",
         "qsfi": 0.00012, "t1": 0.0001, "t2": 0.00014},
    ]


def test_trend_endpoint_400_when_insufficient_analyses(monkeypatch):
    monkeypatch.setattr(trend_service, "list_analyses", lambda: [])

    with TestClient(app) as client:
        response = client.get("/trend", params={"days": 5})

    assert response.status_code == 400


def test_risk_endpoint_still_works_after_the_trend_response_change(monkeypatch):
    analyses = [
        _analysis("day1.csv", "2026-01-01T00:00:00+00:00", [(6, 100.0, 100.0, 100.0)]),
        _analysis("day2.csv", "2026-01-02T00:00:00+00:00", [(6, 40.0, 40.0, 40.0)]),
    ]
    _install_fake_history(monkeypatch, analyses)

    with TestClient(app) as client:
        response = client.get("/risk", params={"days": 2})

    assert response.status_code == 200
    body = response.json()

    (result,) = body["risk_results"]
    assert result["qubit"] == 6
    assert result["risk_level"] == "High"
    # The risk endpoint's own schema (RiskResult) never declared `history`,
    # and still shouldn't now that QubitTrend has it.
    assert "history" not in result
