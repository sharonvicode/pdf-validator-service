"""Respuestas de error en formato RFC 9457 (application/problem+json)."""

from fastapi import Request
from fastapi.responses import JSONResponse

PROBLEM_JSON = "application/problem+json"


def problem_response(
    request: Request, status: int, type_: str, title: str, detail: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type=PROBLEM_JSON,
        content={
            "type": type_,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": request.url.path,
        },
    )
