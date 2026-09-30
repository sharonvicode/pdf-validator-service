import pytest

from app.utils.validators import (
    EmptyFileError,
    FileTooLargeError,
    InvalidPDFError,
    UnsupportedFileTypeError,
    validate_pdf,
)

MAX_SIZE = 1024 * 1024
PDF_MIME = "application/pdf"


def test_valid_pdf_passes(valid_pdf):
    validate_pdf("documento.pdf", PDF_MIME, valid_pdf, MAX_SIZE)


def test_extension_is_case_insensitive(valid_pdf):
    validate_pdf("DOCUMENTO.PDF", PDF_MIME, valid_pdf, MAX_SIZE)


def test_rejects_wrong_extension(valid_pdf):
    with pytest.raises(UnsupportedFileTypeError, match="extensión"):
        validate_pdf("documento.txt", PDF_MIME, valid_pdf, MAX_SIZE)


def test_rejects_wrong_content_type(valid_pdf):
    with pytest.raises(UnsupportedFileTypeError, match="tipo de contenido"):
        validate_pdf("documento.pdf", "text/plain", valid_pdf, MAX_SIZE)


def test_rejects_empty_file():
    with pytest.raises(EmptyFileError):
        validate_pdf("documento.pdf", PDF_MIME, b"", MAX_SIZE)


def test_rejects_file_over_max_size():
    content = b"%PDF-" + b"0" * MAX_SIZE
    with pytest.raises(FileTooLargeError):
        validate_pdf("documento.pdf", PDF_MIME, content, MAX_SIZE)


def test_accepts_file_exactly_at_max_size(valid_pdf):
    validate_pdf("documento.pdf", PDF_MIME, valid_pdf, len(valid_pdf))


def test_rejects_content_without_pdf_signature():
    with pytest.raises(UnsupportedFileTypeError, match="no es un PDF"):
        validate_pdf("documento.pdf", PDF_MIME, b"texto cualquiera", MAX_SIZE)


def test_rejects_corrupt_pdf():
    with pytest.raises(InvalidPDFError, match="dañado"):
        validate_pdf("documento.pdf", PDF_MIME, b"%PDF-1.7 basura", MAX_SIZE)


def test_rejects_pdf_without_pages(pdf_without_pages):
    with pytest.raises(InvalidPDFError, match="no tiene páginas"):
        validate_pdf("documento.pdf", PDF_MIME, pdf_without_pages, MAX_SIZE)
