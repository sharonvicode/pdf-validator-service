import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.core.config import Settings, get_settings
from app.main import app

PROBLEM_FIELDS = {"type", "title", "status", "detail", "instance"}
BAD_REQUEST_DETAIL = (
    "La solicitud debe enviar un archivo en el campo 'file' (multipart/form-data)."
)


@pytest.fixture
def client():
    app.dependency_overrides[get_settings] = lambda: Settings(max_file_size_mb=1)
    # Sin re-lanzar excepciones: el test ve la respuesta 500 que recibiría el cliente.
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def post_file(client, name, content, content_type="application/pdf"):
    return client.post("/validate", files={"file": (name, content, content_type)})


def assert_problem(response, status, type_, instance="/validate"):
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert PROBLEM_FIELDS <= body.keys()
    assert body["status"] == status
    assert body["type"] == type_
    assert body["instance"] == instance
    return body


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validate_accepts_valid_pdf(client, valid_pdf):
    response = post_file(client, "documento.pdf", valid_pdf)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"valido": True, "mensaje": "El archivo es un PDF válido."}


def test_validate_accepts_encrypted_pdf(client, encrypted_pdf):
    response = post_file(client, "documento.pdf", encrypted_pdf)
    assert response.status_code == 200


def test_validate_wrong_extension_returns_415(client, valid_pdf):
    assert_problem(
        post_file(client, "documento.txt", valid_pdf),
        415,
        "/errors/unsupported-file-type",
    )


def test_validate_wrong_content_type_returns_415(client, valid_pdf):
    assert_problem(
        post_file(client, "documento.pdf", valid_pdf, "text/plain"),
        415,
        "/errors/unsupported-file-type",
    )


def test_validate_content_without_pdf_signature_returns_415(client):
    assert_problem(
        post_file(client, "documento.pdf", b"texto cualquiera"),
        415,
        "/errors/unsupported-file-type",
    )


def test_validate_empty_file_returns_400(client):
    assert_problem(post_file(client, "documento.pdf", b""), 400, "/errors/empty-file")


def test_validate_file_too_large_returns_413(client):
    content = b"%PDF-" + b"0" * (1024 * 1024)
    assert_problem(
        post_file(client, "documento.pdf", content), 413, "/errors/file-too-large"
    )


def test_validate_corrupt_pdf_returns_422_without_parser_details(client):
    body = assert_problem(
        post_file(client, "documento.pdf", b"%PDF-1.7 basura"),
        422,
        "/errors/invalid-pdf",
    )
    assert body["detail"] == "El PDF está dañado o no se puede leer."


def test_validate_pdf_without_pages_returns_422(client, pdf_without_pages):
    body = assert_problem(
        post_file(client, "documento.pdf", pdf_without_pages),
        422,
        "/errors/invalid-pdf",
    )
    assert body["detail"] == "El PDF no tiene páginas."


def test_validate_without_file_returns_400(client):
    assert_problem(client.post("/validate"), 400, "/errors/bad-request")


def test_validate_malformed_multipart_returns_400(client):
    response = client.post(
        "/validate", content=b"basura", headers={"content-type": "multipart/form-data"}
    )
    body = assert_problem(response, 400, "/errors/bad-request")
    assert body["detail"] == BAD_REQUEST_DETAIL


def test_unknown_route_returns_404(client):
    assert_problem(client.get("/no-existe"), 404, "/errors/not-found", "/no-existe")


def test_wrong_method_returns_405_with_allow_header(client):
    response = client.get("/validate")
    assert_problem(response, 405, "/errors/method-not-allowed")
    assert response.headers["allow"] == "POST"


def test_unexpected_error_returns_500_without_internal_details(
    client, valid_pdf, monkeypatch, caplog
):
    def explode(**_):
        raise RuntimeError(r"fallo en C:\secreto\modulo.py")

    monkeypatch.setattr(main, "validate_pdf", explode)

    response = post_file(client, "documento.pdf", valid_pdf)

    body = assert_problem(response, 500, "/errors/internal")
    assert body["title"] == "Error interno"
    assert "secreto" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text
    # El detalle queda en los logs del servicio.
    assert "secreto" in caplog.text


def test_app_fails_to_start_with_invalid_config(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "0")
    with pytest.raises(ValueError, match="MAX_FILE_SIZE_MB"):
        with TestClient(app):
            pass
