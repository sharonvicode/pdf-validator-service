import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app

PROBLEM_FIELDS = {"type", "title", "status", "detail", "instance"}


@pytest.fixture
def client():
    app.dependency_overrides[get_settings] = lambda: Settings(max_file_size_mb=1)
    yield TestClient(app)
    app.dependency_overrides.clear()


def post_file(client, name, content, content_type="application/pdf"):
    return client.post("/validate", files={"file": (name, content, content_type)})


def assert_problem(response, status):
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert PROBLEM_FIELDS <= body.keys()
    assert body["status"] == status
    assert body["instance"] == "/validate"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validate_accepts_valid_pdf(client, valid_pdf):
    response = post_file(client, "documento.pdf", valid_pdf)
    assert response.status_code == 200
    assert response.json()["valido"] is True


def test_validate_wrong_extension_returns_415(client, valid_pdf):
    assert_problem(post_file(client, "documento.txt", valid_pdf), 415)


def test_validate_wrong_content_type_returns_415(client, valid_pdf):
    assert_problem(post_file(client, "documento.pdf", valid_pdf, "text/plain"), 415)


def test_validate_empty_file_returns_400(client):
    assert_problem(post_file(client, "documento.pdf", b""), 400)


def test_validate_file_too_large_returns_413(client):
    content = b"%PDF-" + b"0" * (1024 * 1024)
    assert_problem(post_file(client, "documento.pdf", content), 413)


def test_validate_corrupt_pdf_returns_422(client):
    assert_problem(post_file(client, "documento.pdf", b"%PDF-1.7 basura"), 422)


def test_validate_without_file_returns_400(client):
    assert_problem(client.post("/validate"), 400)
