"""Respuestas de error en formato RFC 9457 (application/problem+json)."""

from fastapi import Request
from fastapi.responses import JSONResponse

PROBLEM_JSON = "application/problem+json"
# Esquema OpenAPI del cuerpo que arma problem_response.
PROBLEM_SCHEMA = {
    "type": "object",
    "required": ["type", "title", "status", "detail", "instance"],
    "properties": {
        "type": {"type": "string"},
        "title": {"type": "string"},
        "status": {"type": "integer"},
        "detail": {"type": "string"},
        "instance": {"type": "string"},
    },
}


def problem_response(
    request: Request,
    status: int,
    type_: str,
    title: str,
    detail: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type=PROBLEM_JSON,
        headers=headers,
        content={
            "type": type_,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": request.url.path,
        },
    )
