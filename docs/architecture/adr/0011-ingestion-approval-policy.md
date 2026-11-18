# 0011. Política de aprobación de la ingesta (automática solo en desarrollo)

- Estado: aceptada
- Fecha: 2026-11-18

## Contexto y problema

La constitución (principio I.5) exige que toda versión nueva de una norma se revise antes de quedar
disponible para consultas. En el Sprint 1 no hay un abogado de la OAJ que revise, y el equipo necesita
probar la ingesta y la lectura de punta a punta con rapidez. Al mismo tiempo, **aprobar** (la estructura
es utilizable) no es **verificar** (el texto es la norma vigente).

## Opciones consideradas

1. Aprobación humana siempre (bloquea las pruebas hasta que haya un revisor).
2. Aprobación automática sin más (contradice la constitución y puede llegar a producción por descuido).
3. **Política configurable**: `manual` | `auto_dev`, con `auto_dev` prohibida en staging y producción,
   y con cada aprobación registrando cómo se dio.

## Decisión

Opción 3.

- `DRTC_INGESTION_APPROVAL_POLICY=manual|auto_dev`. Sin valor: `auto_dev` en `local`/`test`, `manual` en
  `staging`/`production`.
- `auto_dev` se rechaza al arrancar (validación de `Settings`) y en el dominio (`ApprovalPolicy`) cuando
  `DRTC_ENVIRONMENT` es `staging` o `production`.
- Cada aprobación guarda `approval_mode` (`human` | `auto_dev`), responsable (`system:auto_dev` o el
  nombre del revisor) y fecha. La API y la interfaz muestran el modo ("aprobación automática solo de
  desarrollo"); una aprobación automática nunca se presenta como revisión humana.
- Aprobar **no cambia** `verification_status`: los textos siguen `unverified` y nada se presenta como
  vigente hasta que una persona los verifique contra la fuente oficial.
- Publicar contenido nuevo (otro `content_digest`) devuelve la versión a `pending`.
- El comando `drtc-ingest approve <versión> --reviewer "Nombre"` existe desde el primer día: pasar a
  aprobación manual es cambiar un valor de configuración.

## Consecuencias

- (+) Se puede desarrollar y demostrar sin revisor, sin debilitar la regla en entornos reales.
- (+) El riesgo queda acotado y visible (modo en la API, interfaz, logs de la CLI).
- (−) En desarrollo existen versiones "aprobadas" que ningún humano revisó: nunca deben copiarse a un
  entorno real sin volver a ingerirlas con la política `manual` y revisarlas.

## Enmienda a la constitución

Constitución 1.1.0: el principio I.5 admite la excepción de desarrollo descrita aquí.
