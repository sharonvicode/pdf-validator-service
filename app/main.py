"""Entrada HTTP del PDF Validator Service."""

from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, get_settings
from app.core.errors import problem_response
from app.utils.validators import PDFValidationError, validate_pdf

# (type, title, detail) de cada problema que no viene de la validación del PDF.
BAD_REQUEST = (
    "/errors/bad-request",
    "Solicitud inválida",
    "La solicitud debe enviar un archivo en el campo 'file' (multipart/form-data).",
)
HTTP_PROBLEMS = {
    400: BAD_REQUEST,
    404: (
        "/errors/not-found",
        "Recurso no encontrado",
        "La ruta solicitada no existe.",
    ),
    405: (
        "/errors/method-not-allowed",
        "Método no permitido",
        "El método HTTP no está permitido en esta ruta.",
    ),
}
INTERNAL_ERROR = (
    "/errors/internal",
    "Error interno",
    "Ocurrió un error inesperado al procesar la solicitud.",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Con configuración inválida el servicio no arranca, en vez de fallar en cada request.
    get_settings()
    yield


app = FastAPI(title="PDF Validator Service", version="0.1.0", lifespan=lifespan)


@app.exception_handler(PDFValidationError)
async def handle_pdf_validation_error(request: Request, error: PDFValidationError):
    return problem_response(
        request, error.status_code, error.type, error.title, error.detail
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(request: Request, _: RequestValidationError):
    return problem_response(request, 400, *BAD_REQUEST)


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, error: StarletteHTTPException):
    # Sin un problema propio para el status se usa "about:blank" (RFC 9457 §4.2.1).
    type_, title, detail = HTTP_PROBLEMS.get(
        error.status_code,
        (
            "about:blank",
            HTTPStatus(error.status_code).phrase,
            "No se pudo procesar la solicitud.",
        ),
    )
    return problem_response(
        request, error.status_code, type_, title, detail, error.headers
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, _: Exception):
    # El cliente solo recibe un mensaje genérico. Starlette vuelve a lanzar la
    # excepción después de responder, y el servidor (uvicorn) loguea la traza.
    return problem_response(request, 500, *INTERNAL_ERROR)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/validate")
def validate(
    file: UploadFile = File(...), settings: Settings = Depends(get_settings)
) -> dict:
    # Se lee un byte más que el máximo: alcanza para detectar que se pasa
    # sin cargar en memoria un archivo enorme.
    content = file.file.read(settings.max_file_size_bytes + 1)
    validate_pdf(
        filename=file.filename or "",
        content_type=file.content_type or "",
        content=content,
        max_size_bytes=settings.max_file_size_bytes,
    )
    return {"valido": True, "mensaje": "El archivo es un PDF válido."}
