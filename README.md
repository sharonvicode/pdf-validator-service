# PDF Validator Service

Microservicio de PDF ExtractText que valida los archivos antes de extraer su texto.
Flujo: Cliente → Orchestrator → **Validator** → Extractor → Persistence → MongoDB.

Su única responsabilidad es decir si un archivo es un PDF aceptable. No extrae texto ni guarda nada.

## Contrato HTTP

### `GET /health`

`200 OK` → `{"status": "ok"}`. Indica que el proceso responde; no verifica nada más.

### `POST /validate`

Request `multipart/form-data` con el archivo en el campo **`file`**:

- nombre terminado en `.pdf` (sin importar mayúsculas);
- `Content-Type` de la parte **exactamente** `application/pdf` (el cliente debe enviarlo explícito;
  httpx/requests mandan `application/octet-stream` si no se indica);
- como máximo `MAX_FILE_SIZE_MB` (10 MiB = 10 485 760 bytes por defecto).

```bash
curl -X POST http://localhost:8001/validate -F "file=@documento.pdf;type=application/pdf"
```

```python
httpx.post(f"{VALIDATOR_URL}/validate", files={"file": (nombre, contenido, "application/pdf")})
```

**PDF válido** → `200 OK`, `application/json`:

```json
{"valido": true, "mensaje": "El archivo es un PDF válido."}
```

Un archivo inválido nunca devuelve 200: el status es la señal.

### Errores (RFC 9457)

Todos los errores, incluidos 404, 405 y 500, se responden como `application/problem+json`
con los campos `type`, `title`, `status`, `detail` e `instance` (la ruta pedida).
**El cliente debe decidir por `type` (o `status`), nunca por `detail`**, que es texto para personas.

Ejemplo:

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json

{"type": "/errors/invalid-pdf", "title": "PDF inválido", "status": 422,
 "detail": "El PDF está dañado o no se puede leer.", "instance": "/validate"}
```

#### El archivo no es un PDF aceptable

Las reglas se aplican en este orden; la primera que falla corta la validación.

| # | Regla | Status | `type` | `detail` |
|---|-------|--------|--------|----------|
| 1 | Extensión `.pdf` | 415 | `/errors/unsupported-file-type` | El archivo debe tener extensión .pdf. |
| 2 | `Content-Type: application/pdf` | 415 | `/errors/unsupported-file-type` | El tipo de contenido debe ser application/pdf. |
| 3 | No está vacío | 400 | `/errors/empty-file` | El archivo está vacío. |
| 4 | No supera `MAX_FILE_SIZE_MB` | 413 | `/errors/file-too-large` | El archivo supera el máximo de 10 MB. |
| 5 | Empieza con la firma `%PDF-` | 415 | `/errors/unsupported-file-type` | El contenido del archivo no es un PDF. |
| 6 | Se puede abrir (no está corrupto) | 422 | `/errors/invalid-pdf` | El PDF está dañado o no se puede leer. |
| 7 | Tiene al menos una página | 422 | `/errors/invalid-pdf` | El PDF no tiene páginas. |

Un PDF protegido con contraseña se acepta sin contar páginas: si se puede leer lo decide el Extractor.

#### La solicitud está mal armada (error de integración)

| Caso | Status | `type` | `detail` |
|------|--------|--------|----------|
| Falta el campo `file` o el multipart está mal formado | 400 | `/errors/bad-request` | La solicitud debe enviar un archivo en el campo 'file' (multipart/form-data). |
| Ruta inexistente | 404 | `/errors/not-found` | La ruta solicitada no existe. |
| Método no permitido (incluye el header `Allow`) | 405 | `/errors/method-not-allowed` | El método HTTP no está permitido en esta ruta. |

#### Error inesperado

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/problem+json

{"type": "/errors/internal", "title": "Error interno", "status": 500,
 "detail": "Ocurrió un error inesperado al procesar la solicitud.", "instance": "/validate"}
```

La respuesta nunca incluye la excepción, rutas locales ni trazas; la traza queda en el log de uvicorn.

#### Disponibilidad

Validator no genera 502, 503 ni 504. Si el servicio está caído, no responde a tiempo o hay un proxy
en el medio, el cliente puede recibir esos status (posiblemente sin problem+json), un timeout o
un error de conexión. Validator no reintenta nada.

### Cómo debe interpretarlo Orchestrator

| Resultado | Significado | ¿Reintentar? |
|-----------|-------------|--------------|
| `200` | PDF válido: seguir con Extractor | — |
| `400 /errors/empty-file`, `413`, `415`, `422` | PDF inválido: informar al cliente | No |
| `400 /errors/bad-request`, `404`, `405` | Bug de integración en Orchestrator | No |
| `500` | Falla interna de Validator | No (como mucho una vez) |
| `502`/`503`/`504`, timeout, conexión rechazada | Validator no disponible | Sí, con backoff |

Timeouts sugeridos en Orchestrator: conexión 2 s, total 15 s. Validator no define timeouts propios
(usa los de uvicorn por defecto).

## Variables de entorno

| Variable | Default | Uso |
|----------|---------|-----|
| `MAX_FILE_SIZE_MB` | `10` | Tamaño máximo aceptado, en MiB. Debe ser un entero mayor que cero: si no, el servicio no arranca. |
| `PORT` | `8000` | Puerto dentro del contenedor (lo usa el `CMD` del Dockerfile). |

## Arquitectura

- `app/main.py`: rutas, arranque y traducción de errores a RFC 9457.
- `app/core/config.py`: configuración desde variables de entorno.
- `app/core/errors.py`: respuestas `application/problem+json`.
- `app/utils/validators.py`: reglas de validación (no depende de FastAPI).
- `tests/`: tests de reglas, configuración y contrato HTTP con PDFs reales generados con pypdf.

## Cómo correrlo

- Instalar: `uv sync` (si el repo está en OneDrive: `UV_LINK_MODE=copy uv sync`)
- Tests: `uv run pytest`
- Servidor: `uv run uvicorn app.main:app --reload --port 8001`
- Docker: `docker build -t pdf-validator-service .` y `docker run --rm -p 8001:8000 pdf-validator-service`

Decisiones de diseño: ver `docs/decisiones.md`.
