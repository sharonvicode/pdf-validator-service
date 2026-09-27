from io import BytesIO

import pytest
from fastapi import UploadFile

from app.utils.validators import FileValidator


def crear_archivo(nombre, tipo, contenido):
    archivo = UploadFile(
        file=BytesIO(contenido),
        filename=nombre,
        headers={"content-type": tipo}
    )
    return archivo


def test_pdf_valido():
    archivo = crear_archivo(
        "documento.pdf",
        "application/pdf",
        b"contenido pdf"
    )

    FileValidator.validate_pdf(archivo)


def test_extension_incorrecta():
    archivo = crear_archivo(
        "documento.txt",
        "application/pdf",
        b"contenido"
    )

    with pytest.raises(Exception):
        FileValidator.validate_pdf(archivo)


def test_tipo_incorrecto():
    archivo = crear_archivo(
        "documento.pdf",
        "text/plain",
        b"contenido"
    )

    with pytest.raises(Exception):
        FileValidator.validate_pdf(archivo)


def test_archivo_demasiado_grande():
    contenido = b"x" * 10485761

    archivo = crear_archivo(
        "documento.pdf",
        "application/pdf",
        contenido
    )

    with pytest.raises(Exception):
        FileValidator.validate_pdf(archivo)