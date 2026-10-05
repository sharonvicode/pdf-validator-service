"""Entrada HTTP del PDF Validator Service."""

from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError

from app.core.config import Settings, get_settings
from app.core.errors import problem_response
from app.utils.validators import PDFValidationError, validate_pdf

app = FastAPI(title="PDF Validator Service", version="0.1.0")


@app.exception_handler(PDFValidationError)
async def handle_pdf_validation_error(request: Request, error: PDFValidationError):
    return problem_response(
        request, error.status_code, error.type, error.title, error.detail
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(request: Request, _: RequestValidationError):
    return problem_response(
        request,
        400,
        "/errors/bad-request",
        "Solicitud inválida",
        "La solicitud debe enviar un archivo en el campo 'file' (multipart/form-data).",
    )


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
