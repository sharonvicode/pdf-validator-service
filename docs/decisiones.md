# Decisiones de diseño

El contrato completo está en el README. Acá queda el porqué de cada decisión.

## 1. Un solo endpoint: `POST /validate`, multipart con campo `file`

Es lo que ya existía y alcanza para Orchestrator. No se versiona la ruta (`/v1`) ni se agregan
endpoints mientras no haya un segundo consumidor ni un cambio incompatible (YAGNI).

## 2. Respuesta exitosa: `200 {"valido": true, "mensaje": "..."}`

Se mantiene la forma actual para no romper a nadie. Un archivo inválido nunca devuelve 200,
así que el status alcanza para decidir; el body es informativo. Se descartaron `204` sin body
y renombrar los campos al inglés porque no aportan nada a la integración.

## 3. Extensión `.pdf` y `Content-Type: application/pdf` estrictos

Orchestrator controla su cliente HTTP y envía `application/pdf` explícito. Aceptar
`application/octet-stream` haría más permisiva la regla sin necesidad. La firma `%PDF-` y la
lectura con pypdf siguen siendo la validación real del contenido.

## 4. Se mantienen los status y `type` de validación (400/413/415/422)

Ya estaban implementados y testeados, y cada status describe bien el caso. Se descartó unificar
todo en 422: simplifica poco y pierde información. Para Orchestrator, cualquier 4xx de
validación significa "PDF inválido". El caso que comparte status (400) se distingue por `type`:
`/errors/empty-file` es un archivo inválido y `/errors/bad-request` es un request mal armado.

## 5. Todos los errores en RFC 9457 (`application/problem+json`)

Antes, 404, 405, el multipart mal formado y los errores inesperados salían con el formato por
defecto de FastAPI/Starlette (`{"detail": ...}` o `text/plain`). Ahora un único helper
(`problem_response`) arma todas las respuestas de error:

- Un handler de `HTTPException` de Starlette cubre 400, 404 y 405 y conserva sus headers
  (el `Allow` del 405). Un status sin problema propio usa `type: "about:blank"` (RFC 9457 §4.2.1).
- Un handler de `Exception` devuelve un 500 genérico.
- Los `type` son URIs relativas (`/errors/...`), que RFC 9457 permite. No hay documentación
  publicada en esas rutas.
- `instance` es la ruta pedida, como ya se hacía.

## 6. Los 500 no exponen detalles; la traza queda en los logs

El body del 500 es fijo. Starlette vuelve a lanzar la excepción después de usar el handler, y
uvicorn la loguea con su traza ("Exception in ASGI application"). Se probó loguear también desde
la app, pero la traza salía duplicada, así que se dejó un único registro: el del servidor. El test
`test_unexpected_error_reaches_the_server_to_be_logged` verifica que la excepción llega al servidor.

## 7. Mensajes públicos en español

`title` y `detail` están en español porque el cliente decide por `type` y `status`.

## 8. Configuración validada al arrancar

`MAX_FILE_SIZE_MB` tiene que ser un entero mayor que cero. `Settings` valida el valor y
`get_settings` traduce un valor no numérico al mismo mensaje. Un hook `lifespan` llama a
`get_settings()` al arrancar, así uvicorn termina con "Application startup failed" en lugar de
responder 500 (o 413 a todo) en cada request. La configuración se sigue leyendo en cada request
vía `Depends`, lo que permite sobreescribirla en los tests.

## 9. Disponibilidad fuera de Validator

Validator no expone un 503 artificial ni reintenta. Los timeouts, los errores de conexión y los
502/503/504 de la infraestructura los maneja Orchestrator (ver la tabla del README).

## 10. Limitación conocida: el límite de tamaño no frena la subida

Starlette recibe el multipart completo antes de llegar al endpoint. `read(max + 1)` evita cargar
en memoria más de lo necesario, pero un archivo enorme igual viaja por la red y se guarda en un
temporal. Si hace falta cortar antes, conviene limitar el body en un proxy o en Orchestrator,
que ya conoce el tamaño del archivo.
