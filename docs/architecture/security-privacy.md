# Seguridad y privacidad

## Estado actual (MVP sin login, ADR-0007)

- Todos los usuarios son anónimos; el navegador envía un identificador aleatorio (`X-Session-Id`)
  que no contiene datos personales y que el backend valida como UUID.
- Solo se expone a la red interna o detrás del proxy de la DRTC mientras dure la etapa de pruebas.
- CORS limitado a los orígenes configurados (`DRTC_CORS_ALLOWED_ORIGINS`).

## Controles

| Riesgo | Control |
|---|---|
| Filtración de claves | Claves solo en el backend (variables `DRTC_*`), `.env` ignorado por git, hook gitleaks, nunca en el frontend |
| Datos personales enviados a terceros | Solo pasajes de evidencia al proveedor; minimización de DNI, placas y nombres (spec 005); Ley N.° 29733 |
| Lo que la gente busca (spec 004) | El texto de una búsqueda **no se guarda ni se registra** (solo su tamaño, el modo y la latencia); las respuestas 422 no lo devuelven; la aplicación, `uvicorn` y `nginx` no escriben la cadena de consulta ni el `Referer`; la interfaz avisa que puede enviarse a un servicio externo y pide no escribir datos personales; escribir en el encabezado nunca llega al proveedor. Verificado con el stack real (0 apariciones de un texto sensible inventado en los registros) |
| Clave de API en errores o registros | `SecretStr`; los errores del proveedor son mensajes fijos (sin clave ni texto enviado); el proveedor falso se rechaza en staging/producción |
| Gasto no intencionado | Todo comando que envía texto a OpenAI imprime la estimación y pide confirmación; sin `--yes` en una terminal no interactiva **no envía nada** |
| Prompt injection desde documentos | Documentos tratados como datos, delimitados; salida validada contra esquema; citas validadas |
| Respuestas engañosas | Validación de citas, abstención, sello de vigencia, aviso "orientativo" |
| Errores que filtran detalles | RFC 9457 con mensaje genérico en 500; detalle solo en logs con `request_id` |
| Contenedores | Imágenes no-root, healthchecks, puertos ligados a 127.0.0.1 en desarrollo |
| Dependencias | Versiones fijadas en `uv.lock` y `package-lock.json`; actualización periódica |
| Auditoría | `request_id` en cada respuesta y log; registro de consultas y uso del proveedor (spec 005) |

## Proveedor de IA (OpenAI)

Antes de la spec 005: revisar la política de retención y uso de datos de la API, evaluar opciones de
retención reducida si aplican, y definir con la DRTC qué datos de expedientes pueden enviarse. Se
registran proveedor, modelo, versión del prompt, tokens y latencia, sin guardar contenido sensible
innecesario.

## Futuro (specs 007 y 010)

- Login con la sesión del sistema DRTC o OIDC; roles (OAJ, SDT, DCT…) → permisos.
- Modo público: límites de solicitudes, protección contra abuso y bots, TLS, monitoreo.
