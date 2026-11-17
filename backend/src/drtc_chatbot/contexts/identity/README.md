# Contexto `identity` — Identidad y acceso (subdominio genérico)

**Responsabilidad:** convertir credenciales en un `Actor` (definido en el shared kernel) y, más adelante,
mapear roles de la DRTC (OAJ, SDT, DCT…) a permisos del asistente.

**Hoy (ADR-0007):** sin login. `AnonymousIdentityProvider` trata a todos como anónimos y conserva un
identificador de sesión del navegador (UUID) si es válido.

**Futuro (spec 007):** adaptador que valide la sesión del sistema DRTC existente (`/api/v1/auth/me`) u
OIDC. Se reemplaza en `bootstrap/container.py` sin tocar ningún caso de uso.
