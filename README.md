# PDF Validator Service

Microservicio encargado de validar archivos PDF antes de que continúen al resto del sistema.

## Funciones

El servicio verifica:

* Que el archivo tenga extensión `.pdf`.
* Que el tipo de contenido sea `application/pdf`.
* Que el archivo no supere los 10 MB.

Si el archivo es válido, devuelve:

```json
{
  "valido": true,
  "mensaje": "El archivo PDF es válido"
}
```

## Endpoints

### Health check

```text
GET /health
```

Respuesta:

```json
{
  "status": "ok"
}
```

### Validar PDF

```text
POST /validate
```

El archivo debe enviarse mediante `multipart/form-data` usando el campo `file`.

## Ejecución local

Crear y activar el entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install fastapi uvicorn python-multipart pytest
```

Ejecutar el servicio:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

El servicio queda disponible en:

```text
http://localhost:8001
```

## Tests

Para ejecutar las pruebas:

```powershell
pytest
```

## Docker

El servicio utiliza el puerto `8001`.

```text
8001:8001
```
