# 0007. Sin autenticación en el MVP; puerto de identidad

- Estado: aceptada
- Fecha: 2026-11-17

## Contexto y problema

En esta etapa se busca probar bien la funcionalidad, sin login. Más adelante podría requerirse login
para personal o ciudadanía, o integrarse con el sistema DRTC existente (usuarios y roles OAJ, SDT,
DCT…, JWT HS256 con `/api/v1/auth/me`).

## Decisión

- Todo caso de uso recibe un `Actor` (shared kernel). La conversión de credenciales a `Actor` es un
  puerto, `IdentityProvider`.
- Hoy: `AnonymousIdentityProvider` (contexto `identity`); conserva un identificador de sesión del
  navegador (UUID) para agrupar conversaciones anónimas.
- Mañana (spec 007): un adaptador que valide la sesión del sistema DRTC u OIDC, sustituido en
  `bootstrap/container.py` sin cambiar casos de uso ni routers.

## Consecuencias

- (+) Agregar login es enchufar un adaptador, no una reescritura.
- (−) Mientras no haya login, el despliegue debe quedar en red interna o detrás del proxy de la DRTC.
