"""Reglas de validación de un archivo PDF.

No depende de FastAPI: recibe los datos del archivo y lanza un
PDFValidationError con el código HTTP que corresponde a cada regla.
"""

from io import BytesIO

from pypdf import PdfReader

PDF_EXTENSION = ".pdf"
PDF_MIME_TYPE = "application/pdf"
PDF_SIGNATURE = b"%PDF-"


class PDFValidationError(Exception):
    status_code = 400
    type = "/errors/invalid-file"
    title = "Archivo inválido"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class EmptyFileError(PDFValidationError):
    status_code = 400
    type = "/errors/empty-file"
    title = "Archivo vacío"


class FileTooLargeError(PDFValidationError):
    status_code = 413
    type = "/errors/file-too-large"
    title = "Archivo demasiado grande"


class UnsupportedFileTypeError(PDFValidationError):
    status_code = 415
    type = "/errors/unsupported-file-type"
    title = "Tipo de archivo no soportado"


class InvalidPDFError(PDFValidationError):
    status_code = 422
    type = "/errors/invalid-pdf"
    title = "PDF inválido"


def validate_pdf(
    filename: str, content_type: str, content: bytes, max_size_bytes: int
) -> None:
    """Lanza PDFValidationError si el archivo no es un PDF aceptable."""
    _check_extension(filename)
    _check_content_type(content_type)
    _check_not_empty(content)
    _check_size(content, max_size_bytes)
    _check_signature(content)
    _check_has_pages(content)


def _check_extension(filename: str) -> None:
    if not filename.lower().endswith(PDF_EXTENSION):
        raise UnsupportedFileTypeError("El archivo debe tener extensión .pdf.")


def _check_content_type(content_type: str) -> None:
    if content_type != PDF_MIME_TYPE:
        raise UnsupportedFileTypeError(
            f"El tipo de contenido debe ser {PDF_MIME_TYPE}."
        )


def _check_not_empty(content: bytes) -> None:
    if not content:
        raise EmptyFileError("El archivo está vacío.")


def _check_size(content: bytes, max_size_bytes: int) -> None:
    if len(content) > max_size_bytes:
        max_mb = max_size_bytes // (1024 * 1024)
        raise FileTooLargeError(f"El archivo supera el máximo de {max_mb} MB.")


def _check_signature(content: bytes) -> None:
    if not content.startswith(PDF_SIGNATURE):
        raise UnsupportedFileTypeError("El contenido del archivo no es un PDF.")


def _check_has_pages(content: bytes) -> None:
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            # Un PDF protegido es válido como archivo; si se puede leer
            # o no con contraseña lo decide el Extractor.
            return
        page_count = len(reader.pages)
    except Exception as error:  # pypdf lanza distintos tipos según el daño
        raise InvalidPDFError("El PDF está dañado o no se puede leer.") from error

    if page_count == 0:
        raise InvalidPDFError("El PDF no tiene páginas.")
