import os
from pathlib import Path

import pytest

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent))

pytestmark = pytest.mark.skipif(
    not ((DATA_DIR / "movies_app.csv").exists() and (DATA_DIR / "mat.npz").exists()),
    reason="movies_app.csv and mat.npz not found. Run the notebook first.",
)


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api import app

    return TestClient(app)


@pytest.fixture(scope="module")
def known_title(client):
    return client.get("/popular", params={"n": 1}).json()[0]["title"]


def test_popular_returns_requested_number(client):
    r = client.get("/popular", params={"n": 5})
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_popular_rejects_bad_n(client):
    assert client.get("/popular", params={"n": 0}).status_code == 422
    assert client.get("/popular", params={"n": 1000}).status_code == 422


def test_search_finds_known_title(client, known_title):
    r = client.get("/search", params={"q": known_title})
    assert r.status_code == 200
    results = r.json()
    assert 1 <= len(results) <= 8
    assert any(known_title.lower() in x["title"].lower() for x in results)


def test_search_requires_a_query(client):
    assert client.get("/search", params={"q": ""}).status_code == 422


def test_recommend_unknown_title_is_404(client):
    r = client.get("/recommend", params={"title": "this movie does not exist 123"})
    assert r.status_code == 404


def test_recommend_respects_n_and_excludes_input(client, known_title):
    r = client.get("/recommend", params={"title": known_title, "n": 5})
    assert r.status_code == 200
    body = r.json()
    movie, recs = body["movie"], body["recommendations"]
    assert len(recs) <= 5
    for rec in recs:
        assert (rec["title"], rec["year"]) != (movie["title"], movie["year"])
        assert 0 <= rec["match"] <= 1


def test_recommend_rejects_bad_n(client, known_title):
    assert client.get("/recommend", params={"title": known_title, "n": 0}).status_code == 422
    assert client.get("/recommend", params={"title": known_title, "n": 500}).status_code == 422