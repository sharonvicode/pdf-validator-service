from io import BytesIO

import pytest
from pypdf import PdfWriter


def build_pdf(pages: int, password: str | None = None) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    if password:
        writer.encrypt(password)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture
def valid_pdf() -> bytes:
    return build_pdf(pages=1)


@pytest.fixture
def pdf_without_pages() -> bytes:
    return build_pdf(pages=0)


@pytest.fixture
def encrypted_pdf() -> bytes:
    return build_pdf(pages=1, password="secreta")
