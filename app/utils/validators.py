from fastapi import HTTPException, UploadFile

from app.core.config import MAX_FILE_SIZE


PDF_EXTENSION = ".pdf"
PDF_CONTENT_TYPE = "application/pdf"


class FileValidator:

    @staticmethod
    def validate_pdf(file: UploadFile) -> None:

        if not file.filename or not file.filename.lower().endswith(PDF_EXTENSION):
            raise HTTPException(
                status_code=400,
                detail="El archivo debe tener extensión .pdf"
            )

        if file.content_type != PDF_CONTENT_TYPE:
            raise HTTPException(
                status_code=400,
                detail="El archivo debe ser tipo application/pdf"
            )

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE} bytes"
            )