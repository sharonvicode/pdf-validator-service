from fastapi import FastAPI, File, UploadFile

from app.utils.validators import FileValidator


app = FastAPI(title="PDF Validator Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate")
def validate_pdf(file: UploadFile = File(...)):
    FileValidator.validate_pdf(file)

    return {
        "valido": True,
        "mensaje": "El archivo PDF es válido"
    }