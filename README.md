# PDF Validator Service

Microservicio de PDF ExtractText que valida los archivos antes de extraer su texto.
Flujo: Cliente → Orchestrator → **Validator** → Extractor → Persistence → MongoDB.

Su única responsabilidad es decir si un archivo es un PDF aceptable. No extrae texto ni guarda nada.

## Reglas de validación

Se aplican en este orden; la primera que falla corta la validación.

| # | Regla | Código HTTP |
|---|-------|-------------|
| 1 | Extensión `.pdf` (sin importar mayúsculas) | 415 |
| 2 | Tipo de contenido `application/pdf` | 415 |
| 3 | El archivo no está vacío | 400 |
| 4 | No supera `MAX_FILE_SIZE_MB` (10 MB por defecto) | 413 |
| 5 | Empieza con la firma `%PDF-` | 415 |
| 6 | Se puede abrir y tiene al menos una página | 422 |

Un PDF protegido con contraseña se acepta: si se puede leer lo decide el Extractor.

## Endpoints

- `GET /health` → `{"status": "ok"}`
- `POST /validate`: recibe el PDF como `multipart/form-data` en el campo `file`.
  - 200: `{"valido": true, "mensaje": "El archivo es un PDF válido."}`
  - Errores en formato RFC 9457 (`application/problem+json`) con los campos
    `type`, `title`, `status`, `detail` e `instance`.

El formato de la respuesta exitosa y el idioma de los campos quedan sujetos a la reunión de contratos.

## Arquitectura

- `app/main.py`: rutas y traducción de errores a RFC 9457.
- `app/core/config.py`: configuración desde variables de entorno.
- `app/core/errors.py`: respuestas `application/problem+json`.
- `app/utils/validators.py`: reglas de validación (no depende de FastAPI).
- `tests/`: 20 tests con PDFs reales generados con pypdf.

## Variables de entorno

| Variable | Default | Uso |
|----------|---------|-----|
| `MAX_FILE_SIZE_MB` | `10` | Tamaño máximo aceptado |
| `PORT` | `8000` | Puerto dentro del contenedor |

## Cómo correrlo

- Instalar: `uv sync`
- Tests: `uv run pytest`
- Servidor: `uv run uvicorn app.main:app --reload --port 8001`
- Docker: `docker build -t pdf-validator-service .` y `docker run --rm -p 8001:8000 pdf-validator-service`

Decisiones de diseño: ver `docs/decisiones.md`.
